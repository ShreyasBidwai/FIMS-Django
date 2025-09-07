// =============================
// Family Head - State/City Dropdown
// =============================
$(document).ready(function() {
    $("#head_state").change(function() {
        var stateId = $(this).val();
        $("#head_city").empty().append('<option value="">Select City</option>');
        if (stateId) {
            $.ajax({
                url: "/city/",
                data: { "state_id": stateId },
                success: function(data) {
                    $.each(data, function(index, city) {
                        $("#head_city").append('<option value="' + city.id + '">' + city.name + '</option>');
                    });
                }
            });
        }
    });
});

// =============================
// Family Head - Wedding Date Toggle
// =============================
document.addEventListener('DOMContentLoaded', () => {
    const marriedRadio = document.querySelector('input[name="head_marital_status"][value="Married"]');
    const unmarriedRadio = document.querySelector('input[name="head_marital_status"][value="Unmarried"]');
    const weddingDateRow = document.getElementById('wedding_date_row');
    const weddingDate = document.getElementById('wedding_date');

    function updateHeadWeddingDate() {
        if (marriedRadio && marriedRadio.checked) {
            weddingDateRow.style.display = '';
        } else {
            weddingDateRow.style.display = 'none';
        }
    }
    if (marriedRadio && unmarriedRadio) {
        marriedRadio.addEventListener('change', updateHeadWeddingDate);
        unmarriedRadio.addEventListener('change', updateHeadWeddingDate);
        updateHeadWeddingDate();
    }
});

// =============================
// Hobby Add Function
// =============================
window.addHobby = function() {
    const section = document.getElementById("hobbies-section");
    const input = document.createElement("input");
    input.type = "text";
    input.name = "head_hobbies[]";
    input.placeholder = "Enter a hobby";
    input.classList.add("hobby-input");
    section.appendChild(input);
};

// =============================
// Add Member Function (simplified for now)
// =============================
let memberIndex = 0;
window.addMember = function() {
    memberIndex++;
    const container = document.getElementById("members-container");
    const div = document.createElement("div");
    div.className = "member-form";

    div.innerHTML = `
        <fieldset>
            <legend>Member ${memberIndex}</legend>
            <div>
                <label>Name:</label>
                <input type="text" name="member_${memberIndex}_name" placeholder="Name" maxlength="50">
                <span class="error-message"></span>
            </div>
            <div>
                <label>Surname:</label>
                <input type="text" name="member_${memberIndex}_surname" placeholder="Surname" maxlength="50">
                <span class="error-message"></span>
            </div>
            <div>
                <label>Gender:</label>
                <label><input type="radio" name="member_${memberIndex}_gender" value="Male"> Male</label>
                <label><input type="radio" name="member_${memberIndex}_gender" value="Female"> Female</label>
                <span class="error-message"></span>
            </div>
            <div>
                <label>Relationship to Head:</label>
                <input type="text" name="member_${memberIndex}_relationship" placeholder="Relationship" maxlength="50">
                <span class="error-message"></span>
            </div>
            <div>
                <label>Birthdate:</label>
                <input type="date" name="member_${memberIndex}_birthdate">
                <span class="error-message"></span>
            </div>
            <div>
                <label>Mobile No (optional):</label>
                <input type="text" name="member_${memberIndex}_mobile" maxlength="10">
                <span class="error-message"></span>
            </div>
            <div>
                <label>Photo:</label>
                <input type="file" name="member_${memberIndex}_photo" accept="image/png, image/jpeg">
                <span class="error-message"></span>
            </div>
            <div>
                <label for="member_${memberIndex}_education">Education:</label>
                <select name="member_${memberIndex}_education" id="member_${memberIndex}_education">
                    <option value="">Select</option>
                    <option value="Graduate">Graduate</option>
                    <option value="Post Graduate">Post Graduate</option>
                    <option value="Diploma">Diploma</option>
                </select>
                <span class="error-message"></span>
            </div>
            <div>
                <label>Marital Status:</label>
                <label><input type="radio" name="member_${memberIndex}_marital_status" value="Married"> Married</label>
                <label><input type="radio" name="member_${memberIndex}_marital_status" value="Unmarried"> Unmarried</label>
                <span class="error-message"></span>
            </div>
            <div id="member_${memberIndex}_wedding_date_row" style="display:none;">
                <label for="member_${memberIndex}_wedding_date">Wedding Date:</label>
                <input type="date" name="member_${memberIndex}_wedding_date" id="member_${memberIndex}_wedding_date">
                <span class="error-message"></span>
            </div>
        </fieldset>
    `;

    container.appendChild(div);
};

// =============================
// Validation Logic
// =============================
function showError(id, message) {
    document.getElementById(id).textContent = `* ${message}`;
}

function clearErrors() {
    document.querySelectorAll(".error-message").forEach(el => el.textContent = "");
}

function validateForm(event) {
    clearErrors();
    let valid = true;

    const name = document.getElementById("head_name").value.trim();
    if (name.length === 0 || name.length > 50) {
        showError("error-head_name", "Name is required (max 50 chars).");
        valid = false;
    }

    const surname = document.getElementById("head_surname").value.trim();
    if (surname.length === 0 || surname.length > 50) {
        showError("error-head_surname", "Surname is required (max 50 chars).");
        valid = false;
    }

    const birthdate = document.getElementById("head_birthdate").value;
    if (!birthdate) {
        showError("error-head_birthdate", "Birthdate is required.");
        valid = false;
    } else {
        const age = Math.floor((Date.now() - new Date(birthdate)) / (365.25 * 24 * 60 * 60 * 1000));
        if (age < 21) {
            showError("error-head_birthdate", "Head must be 21+ years.");
            valid = false;
        }
    }

    const mobile = document.getElementById("head_mobile").value.trim();
    if (!/^\d{10}$/.test(mobile)) {
        showError("error-head_mobile", "Enter a valid 10-digit mobile number.");
        valid = false;
    }

    const pincode = document.getElementById("head_pincode").value.trim();
    if (!/^\d{6}$/.test(pincode)) {
        showError("error-head_pincode", "Enter a valid 6-digit pincode.");
        valid = false;
    }

    // Marital Status
    const maritalStatus = document.querySelector("input[name='head_marital_status']:checked");
    if (!maritalStatus) {
        showError("error-head_marital_status", "Select marital status.");
        valid = false;
    }

    // Gender
    const gender = document.querySelector("input[name='head_gender']:checked");
    if (!gender) {
        showError("error-head_gender", "Select gender.");
        valid = false;
    }

    // Wedding Date if married
    if (maritalStatus && maritalStatus.value === "Married") {
        const weddingDate = document.getElementById("wedding_date").value;
        if (!weddingDate) {
            showError("error-head_wedding_date", "Wedding date required for married.");
            valid = false;
        }
    }

    // Education
    const education = document.getElementById("head_education").value;
    if (!education) {
        showError("error-head_education", "Education is required.");
        valid = false;
    }

    // Hobbies
    const hobbies = document.querySelectorAll("input[name='head_hobbies[]']");
    let hasHobby = false;
    hobbies.forEach(h => { if (h.value.trim()) hasHobby = true; });
    if (!hasHobby) {
        showError("error-head_hobbies", "Enter at least one hobby.");
        valid = false;
    }

    // Photo
    const photo = document.querySelector("input[name='head_photo']");
    if (!photo.files[0]) {
        showError("error-head_photo", "Photo required.");
        valid = false;
    } else {
        const file = photo.files[0];
        if (!["image/jpeg", "image/png"].includes(file.type) || file.size > 2 * 1024 * 1024) {
            showError("error-head_photo", "Only JPG/PNG ≤2MB allowed.");
            valid = false;
        }
    }

    if (!valid) event.preventDefault();
    return valid;
}