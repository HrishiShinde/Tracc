(() => {
  const toggle = document.getElementById("dailyReminder");
  const reminderTime = document.getElementById("reminder-time");
  const reminderWrapper = document.getElementById("reminderTimeWrapper");
  const deviceButton = document.getElementById("pushReminderButton");
  if (!toggle || !reminderTime || !reminderWrapper) return;
  const notify = (message, variant = "info") => window.appAlert(message, { variant });

  const csrf = document.cookie.split(";").map(value => value.trim())
    .find(value => value.startsWith("csrftoken="))?.slice("csrftoken=".length);
  const encodeKey = value => {
    const padding = "=".repeat((4 - value.length % 4) % 4);
    const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
    return Uint8Array.from(atob(base64), char => char.charCodeAt(0));
  };

  async function saveSubscription(subscription) {
    const response = await fetch("/push/subscription/", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": decodeURIComponent(csrf || "") },
      body: JSON.stringify({
        subscription: subscription.toJSON(),
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
      }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not save this device's notification settings.");
  }

  async function subscribeThisDevice({ requestPermission = true } = {}) {
    if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
      throw new Error("Push notifications are not supported by this browser.");
    }
    if (Notification.permission === "denied") {
      throw new Error("Notifications are blocked by your browser. Allow them in browser or device settings, then try again.");
    }

    // Request permission immediately from the user's toggle/button action.
    const permission = Notification.permission === "default" && requestPermission
      ? await Notification.requestPermission()
      : Notification.permission;
    if (permission !== "granted") throw new Error("Notification permission was not granted.");

    const registration = await navigator.serviceWorker.ready;
    let subscription = await registration.pushManager.getSubscription();
    let createdHere = false;
    if (!subscription) {
      const configResponse = await fetch("/push/config/");
      const config = await configResponse.json();
      if (!configResponse.ok) throw new Error(config.error || "Push notifications are not configured on the server.");
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: encodeKey(config.publicKey),
      });
      createdHere = true;
    }

    try {
      await saveSubscription(subscription);
    } catch (error) {
      if (createdHere) await subscription.unsubscribe().catch(() => {});
      throw error;
    }
    return { createdHere };
  }

  function updateReminderVisibility() {
    reminderWrapper.classList.toggle("d-none", !toggle.checked);
  }

  async function refreshDeviceControl() {
    updateReminderVisibility();
    if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
      if (deviceButton) deviceButton.classList.add("d-none");
      return;
    }

    const registration = await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    if (toggle.checked && !subscription) {
      if (deviceButton) {
        deviceButton.textContent = "Enable notifications on this device";
        deviceButton.classList.remove("d-none");
      }
    } else if (toggle.checked) {
      if (deviceButton) {
        deviceButton.textContent = "Turn off notifications on this device";
        deviceButton.classList.remove("d-none");
      }
    } else if (subscription) {
      if (deviceButton) {
        deviceButton.textContent = "Remove notifications from this device";
        deviceButton.classList.remove("d-none");
      }
    } else {
      if (deviceButton) deviceButton.classList.add("d-none");
    }
  }

  toggle.addEventListener("change", async () => {
    const enabling = toggle.checked;
    const previous = !enabling;
    toggle.disabled = true;
    try {
      if (enabling) {
        try {
          await subscribeThisDevice();
          const saved = await autoSaveSetting(
            { daily_log: true, reminder_time: reminderTime.value },
            { successMessage: "Daily reminders enabled." }
          );
          if (!saved) toggle.checked = previous;
        } catch (error) {
          toggle.checked = previous;
          notify(error.message || "Could not enable daily reminders.", "error");
        }
      } else {
        const saved = await autoSaveSetting(
          { daily_log: false },
          { successMessage: "Daily reminders paused on all devices." }
        );
        if (!saved) toggle.checked = previous;
      }
      await refreshDeviceControl().catch(() => {});
    } finally {
      toggle.disabled = false;
    }
  });

  reminderTime.addEventListener("change", async () => {
    if (toggle.checked) await autoSaveSetting(
      { reminder_time: reminderTime.value },
      { successMessage: "Reminder time saved." }
    );
  });

  if (deviceButton) {
    deviceButton.addEventListener("click", async () => {
      deviceButton.disabled = true;
      try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.getSubscription();
        if (subscription) {
          const response = await fetch("/push/unsubscribe/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": decodeURIComponent(csrf || "") },
            body: JSON.stringify({ endpoint: subscription.endpoint }),
          });
          if (!response.ok) throw new Error("Could not remove this device's notification settings.");
          await subscription.unsubscribe();
          notify("Notifications removed from this device.", "success");
        } else {
          await subscribeThisDevice();
          notify("Notifications enabled on this device.", "success");
        }
        await refreshDeviceControl();
      } catch (error) {
        notify(error.message || "Could not update this device's notification settings.", "error");
      } finally {
        deviceButton.disabled = false;
      }
    });
  }

  refreshDeviceControl().catch(() => {});
})();
