const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    const goalType = document.getElementById('goal-type');
    const goalRate = document.getElementById('weekly-goal-rate');
    const goalRateHelp = document.getElementById('goal-rate-help');
    const suggestion = document.getElementById('goal-rate-suggestion');
    function syncGoalRate() {
        const maintaining = goalType.value === 'maintain';
        goalRate.disabled = maintaining;
        goalRateHelp.classList.toggle('d-none', maintaining);
        if (maintaining) goalRate.value = '';
    }
    if (goalType.value !== 'maintain' && !goalRate.value) goalRate.value = suggestion.textContent;
    goalType.addEventListener('change', function() {
        syncGoalRate();
        autoSaveSetting({goal_type: this.value, weekly_goal_rate: this.value === 'maintain' ? null : (goalRate.value || suggestion.textContent)});
        if (this.value !== 'maintain' && !goalRate.value) goalRate.value = suggestion.textContent;
    });
    goalRate.addEventListener('change', function() {
        if (Number(this.value) > 0 && Number(this.value) <= 2) {
            autoSaveSetting({weekly_goal_rate: this.value});
        } else {
            window.appAlert('Enter a weekly target greater than 0 and at most 2.', {variant: 'error'});
        }
    });
    syncGoalRate();

    function updateProfileUnitDisplays(weightUnit, heightUnit) {
        const factor = weightUnit === 'lbs' ? 2.20462 : 1;
        const suffix = weightUnit === 'lbs' ? 'lbs' : 'kg';
        document.querySelectorAll('[data-starting-weight-kg]').forEach(el => {
            const raw = parseFloat(el.dataset.startingWeightKg);
            el.value = Number.isFinite(raw) ? (raw * factor).toFixed(1) : '';
        });
        const startUnit = document.getElementById('starting-weight-unit');
        if (startUnit) startUnit.value = suffix;
        const height = document.querySelector('[data-height-cm]');
        if (height) {
            const cm = parseFloat(height.dataset.heightCm);
            height.value = Number.isFinite(cm) ? (heightUnit === 'ft' ? `${Math.floor(cm / 30.48)} ft ${(cm / 2.54 % 12).toFixed(1)} in` : `${cm.toFixed(1)} cm`) : '';
        }
        const identityUnit = document.getElementById('identity-height-unit');
        if (identityUnit) identityUnit.value = heightUnit;
    }
    updateProfileUnitDisplays(document.getElementById('weight-unit').value, document.getElementById('height-unit').value);

    // Weight Unit.
    document.getElementById("weight-unit").addEventListener("change", function() {
        updateProfileUnitDisplays(this.value, document.getElementById('height-unit').value);
        document.getElementById('goal-rate-unit').textContent = this.value;
        document.getElementById('goal-rate-help-unit').textContent = this.value;
        suggestion.textContent = this.value === 'lbs' ? '1.1' : '0.5';
        if (goalType.value !== 'maintain') goalRate.value = suggestion.textContent;
        let payload = {
            "weight_unit": this.value,
            ...(goalType.value !== 'maintain' ? {"weekly_goal_rate": goalRate.value} : {})
        }
        autoSaveSetting(payload);
    });
    
    // Height Unit.
    document.getElementById("height-unit").addEventListener("change", function() {
        updateProfileUnitDisplays(document.getElementById('weight-unit').value, this.value);
        let payload = {
            "height_unit": this.value
        }
        autoSaveSetting(payload);
    });

    // Weekly Summary.
    document.getElementById("weeklySummary").addEventListener("change", function() {
        let payload = {
            "weekly_summary": this.checked,
        }
        autoSaveSetting(payload);
    });

    async function postAccountAction(url) {
        return fetch(url, {
            method: 'POST',
            headers: {'X-CSRFToken': decodeURIComponent(csrfToken || ''), 'X-Requested-With': 'XMLHttpRequest'}
        });
    }

    document.querySelectorAll('[data-account-action]').forEach(button => {
        button.addEventListener('click', async function() {
            const deletingAccount = this.dataset.accountAction === 'delete';
            const confirmed = deletingAccount
                ? await window.appConfirm('Permanently delete your account and all associated data? You will not be able to sign in again.', {title: 'Delete your account?', confirmLabel: 'Delete account', danger: true})
                : await window.appConfirm('Permanently delete all weight logs, milestones, weekly summaries, and streak progress? Your account and profile will remain.', {title: 'Reset your data?', confirmLabel: 'Reset data', danger: true});
            if (!confirmed) return;
            this.disabled = true;
            try {
                const endpoint = deletingAccount ? document.body.dataset.deleteAccountUrl : document.body.dataset.resetDataUrl;
                const response = await postAccountAction(endpoint);
                const result = await response.json();
                if (!response.ok || !result.success) throw new Error(result.error || (deletingAccount ? 'Could not delete account.' : 'Could not reset data.'));
                if (deletingAccount) {
                    window.appAlertAfterNavigation('Your account was deleted.', {variant: 'success'});
                    window.location.href = document.body.dataset.loginUrl;
                    return;
                }
                window.appAlert('Your logs and progress have been deleted.', {variant: 'success'});
            } catch (error) {
                window.appAlert(error.message, {variant: 'error'});
                this.disabled = false;
            }
        });
    });

