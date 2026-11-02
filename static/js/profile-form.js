// CONSTANTS
    const KG_TO_LBS = 2.20462;
    const LBS_TO_KG = 1 / KG_TO_LBS;

    const CM_TO_FT = 0.0328084;
    const FT_TO_CM = 30.48;

    // HEIGHT CONVERSION (cm <-> ft + in)
    const heightCmInput = document.getElementById("height_cm");
    const heightFtInput = document.getElementById("height_ft");
    const heightInInput = document.getElementById("height_in");
    const heightUnitSelect = document.getElementById("height-unit");

    function cmToFtIn(cm) {
        const totalInches = cm / 2.54;

        let ft = Math.floor(totalInches / 12);
        let inches = Math.round(totalInches - (ft * 12));

        if (inches === 12) {
            ft += 1;
            inches = 0;
        }

        return { ft, inches };
    }

    function ftInToCm(ft, inches) {
        return (ft * 30.48) + (inches * 2.54);
    }

    function switchHeightMode() {
        if (heightUnitSelect.value === "ft") {

            // Convert cm → ft/in
            if (heightCmInput.value) {
                const result = cmToFtIn(parseFloat(heightCmInput.value));
                heightFtInput.value = result.ft;
                heightInInput.value = result.inches;
            }

            heightCmInput.classList.add("d-none");
            heightFtInput.classList.remove("d-none");
            heightInInput.classList.remove("d-none");

        } else {

            // Convert ft/in → cm
            if (heightFtInput.value || heightInInput.value) {
                heightCmInput.value = ftInToCm(
                    parseInt(heightFtInput.value || 0),
                    parseInt(heightInInput.value || 0)
                ).toFixed(1);
            }

            heightCmInput.classList.remove("d-none");
            heightFtInput.classList.add("d-none");
            heightInInput.classList.add("d-none");
        }
    }

    heightUnitSelect.addEventListener("change", switchHeightMode);
    heightInInput.addEventListener("input", function() {
        if (this.value > 11) {
            const extraFeet = Math.floor(this.value / 12);
            this.value = this.value % 12;
            heightFtInput.value = parseInt(heightFtInput.value || 0) + extraFeet;
        }
    });

    // On page load
    document.addEventListener("DOMContentLoaded", switchHeightMode);

    // Convert BEFORE submit → always store cm
    function normalizeHeightBeforeSubmit() {
        if (heightUnitSelect.value === "ft") {
            heightCmInput.value = ftInToCm(
                parseInt(heightFtInput.value || 0),
                parseInt(heightInInput.value || 0)
            ).toFixed(1);
        }
    }

    // WEIGHT CONVERSION
    function attachWeightConversion(inputId, unitSelectId) {
        const weightInput = document.getElementById(inputId);
        const unitSelect = document.getElementById(unitSelectId);

        let displayedUnit = "kg"; // Profile values are stored in kg.
        function convertDisplay() {
            let value = parseFloat(weightInput.value);
            if (!Number.isFinite(value)) return;

            if (displayedUnit === unitSelect.value) return;
            weightInput.value = (unitSelect.value === "lbs" ? value * KG_TO_LBS : value * LBS_TO_KG).toFixed(1);
            displayedUnit = unitSelect.value;
        }

        function normalizeBeforeSubmit() {
            let value = parseFloat(weightInput.value);
            if (!Number.isFinite(value)) return;

            if (unitSelect.value === "lbs") weightInput.value = (value * LBS_TO_KG).toFixed(1);
        }

        unitSelect.addEventListener("change", convertDisplay);
        if (unitSelect.value !== displayedUnit) convertDisplay();

        return normalizeBeforeSubmit;
    }


    // INIT
    const is_update = document.getElementById("is_update");
    let normalizeCurrentWeight = () => {};

    if (!is_update) {
        normalizeCurrentWeight = attachWeightConversion("current_weight", "current-weight-unit");
    }

    const normalizeTargetWeight = attachWeightConversion("target_weight", "target-weight-unit");

    // FORM SUBMIT
    document.querySelector("form").addEventListener("submit", function() {
        normalizeHeightBeforeSubmit();
        normalizeCurrentWeight();
        normalizeTargetWeight();
    });
