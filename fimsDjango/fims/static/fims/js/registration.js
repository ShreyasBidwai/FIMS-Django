
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

window.addHobby = function() {
    const section = document.getElementById("hobbies-section");
    const input = document.createElement("input");
    input.type = "text";
    input.name = "head_hobbies[]";
    input.placeholder = "Enter a hobby";
    input.classList.add("hobby-input");
    section.appendChild(input);
};

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
                <label>Marital Status:</label>
                <label><input type="radio" name="member_${memberIndex}_marital_status" value="Married"> Married</label>
                <label><input type="radio" name="member_${memberIndex}_marital_status" value="Unmarried"> Unmarried</label>
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
                <label>Relationship to Head:</label>
                <input type="text" name="member_${memberIndex}_relationship" placeholder="Relationship" maxlength="50">
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



function showMemberError(input, message) {
    // Find the closest .error-message after the input (or its parent for radios)
    let errorSpan = null;
    if ($(input).attr('type') === 'radio') {
        // For radio, find the parent div and its .error-message
        errorSpan = $(input).closest('div').find('.error-message').first();
    } else {
        errorSpan = $(input).siblings('.error-message').first();
    }
    if (errorSpan && errorSpan.length) {
        errorSpan.text(message);
    }
}

function clearMemberErrors() {
    $(".member-form .error-message").text("");
}

function validateForm(event) {
    clearMemberErrors();
    let valid = true;

    // Validate head gender
    const headGenderInputs = $("input[name='head_gender']");
    if (!headGenderInputs.is(':checked')) {
        // Find the error-message span after the last gender radio
        const lastGenderInput = headGenderInputs.last();
        let errorSpan = lastGenderInput.closest('td,div').find('.error-message');
        if (!errorSpan.length) {
            // fallback: find next span
            errorSpan = lastGenderInput.parent().next('.error-message');
        }
        errorSpan.text("Gender is required.");
        valid = false;
    } else {
        // Clear error if selected
        const lastGenderInput = headGenderInputs.last();
        let errorSpan = lastGenderInput.closest('td,div').find('.error-message');
        if (!errorSpan.length) {
            errorSpan = lastGenderInput.parent().next('.error-message');
        }
        errorSpan.text("");
    }

    // Validate each member
    $('.member-form').each(function() {
        // Name
        const nameInput = $(this).find('input[name^="member_"][name$="_name"]');
        if (nameInput.length) {
            const nameVal = nameInput.val();
            if (typeof nameVal === 'undefined' || nameVal.trim() === "") {
                showMemberError(nameInput, "Name is required.");
                valid = false;
            }
        }
        // Gender
        const genderInputs = $(this).find('input[type="radio"][name^="member_"][name$="_gender"]');
        if (genderInputs.length && !genderInputs.is(':checked')) {
            // Show error on the first radio in the group
            showMemberError(genderInputs.first(), "Gender is required.");
            valid = false;
        }
        // Relationship
        const relInput = $(this).find('input[name^="member_"][name$="_relationship"]');
        if (relInput.length) {
            const relVal = relInput.val();
            if (typeof relVal === 'undefined' || relVal.trim() === "") {
                showMemberError(relInput, "Relationship is required.");
                valid = false;
            }
        }
    });

    if (!valid) {
        event.preventDefault();
    }
    return valid;
}

// Attach validation to form submit
$(document).ready(function() {
    $('#registrationForm').off('submit').on('submit', validateForm);
});