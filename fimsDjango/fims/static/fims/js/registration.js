// static/js/register.js

// Show/Hide wedding date based on marital status
document.addEventListener('DOMContentLoaded', () => {
    const marriedRadio = document.querySelector('input[name="head_marital_status"][value="Married"]');
    const unmarriedRadio = document.querySelector('input[name="head_marital_status"][value="Unmarried"]');
    const weddingDate = document.getElementById('wedding_date');

    if (marriedRadio && unmarriedRadio) {
        marriedRadio.addEventListener('change', () => {
            weddingDate.style.display = 'inline';
            weddingDate.required = true;
        });

        unmarriedRadio.addEventListener('change', () => {
            weddingDate.style.display = 'none';
            weddingDate.required = false;
        });
    }
});

function addHobby() {
    const section = document.getElementById("hobbies-section");
    const input = document.createElement("input");
    input.type = "text";
    input.name = "head_hobbies[]";
    input.placeholder = "Enter a hobby";
    input.required = true;
    section.appendChild(input);
}

let memberIndex = 0;

function addMember() {
    memberIndex++;

    const container = document.getElementById("members-container");
    const div = document.createElement("div");
    div.className = "member-form";

    div.innerHTML = `
        <fieldset>
            <legend>Member ${memberIndex}</legend>
            <input type="text" name="member_${memberIndex}_name" placeholder="Name" required maxlength="50">
            <input type="text" name="member_${memberIndex}_surname" placeholder="Surname" required maxlength="50">
            <input type="text" name="member_${memberIndex}_relationship" placeholder="Relationship to Head" required maxlength="50">
            <input type="date" name="member_${memberIndex}_birthdate" required>
            <input type="text" name="member_${memberIndex}_mobile" placeholder="Mobile No (optional)" maxlength="10">
            <input type="file" name="member_${memberIndex}_photo" accept="image/png, image/jpeg">

            <label>
                <input type="checkbox" onchange="toggleAddress(this, ${memberIndex})"> Has different address?
            </label>

            <div class="address-fields" id="address_${memberIndex}" style="display:none;">
                <textarea name="member_${memberIndex}_address" placeholder="Address"></textarea>
                <input type="text" name="member_${memberIndex}_state" placeholder="State">
                <input type="text" name="member_${memberIndex}_city" placeholder="City">
                <input type="text" name="member_${memberIndex}_pincode" placeholder="Pincode" maxlength="6">
            </div>
        </fieldset>
    `;

    container.appendChild(div);
}

function toggleAddress(checkbox, index) {
    const addressDiv = document.getElementById(`address_${index}`);
    addressDiv.style.display = checkbox.checked ? 'block' : 'none';
}
