// Family Head - State/City Dropdown

$(document).ready(function(){
    $("#head_state").change(function(){
        var stateId = $(this).val();
        $("#head_city").empty().append('<option value="">Select City</option>');
        if(stateId){
            $.ajax({
                url: "/city/",
                data: { "state_id": stateId },
                success: function(data){
                    $.each(data, function(index, city){
                        $("#head_city").append('<option value="'+city.id+'">'+city.name+'</option>');
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
            weddingDate.required = true;
        } else {
            weddingDateRow.style.display = 'none';
            weddingDate.required = false;
        }
    }
    if (marriedRadio && unmarriedRadio) {
        marriedRadio.addEventListener('change', updateHeadWeddingDate);
        unmarriedRadio.addEventListener('change', updateHeadWeddingDate);
        updateHeadWeddingDate();
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

            <div class="form-row">
                <label for="member_${memberIndex}_education">Education:</label>
                <select name="member_${memberIndex}_education" id="member_${memberIndex}_education" required>
                    <option value="Graduate">Graduate</option>
                    <option value="Post Graduate">Post Graduate</option>
                    <option value="Diploma">Diploma</option>
                </select>
            </div>

            <div class="form-row">
                Marital Status:
                <label><input type="radio" name="member_${memberIndex}_marital_status" value="Married" required> Married</label>
                <label><input type="radio" name="member_${memberIndex}_marital_status" value="Unmarried"> Unmarried</label>
            </div>

            <div id="member_${memberIndex}_wedding_date_row" style="display:none;">
                <label for="member_${memberIndex}_wedding_date">Wedding Date:</label>
                <input type="date" name="member_${memberIndex}_wedding_date" id="member_${memberIndex}_wedding_date">
            </div>

            <label>
                <input type="checkbox" onchange="toggleAddress(this, ${memberIndex})"> Has different address?
            </label>

            <div class="address-fields" id="address_${memberIndex}" style="display:none;">
                <textarea name="member_${memberIndex}_address" placeholder="Address"></textarea>
                <select name="member_${memberIndex}_state" id="member_${memberIndex}_state">
                    <option value="">Select State</option>
                </select>
                <select name="member_${memberIndex}_city" id="member_${memberIndex}_city">
                    <option value="">Select City</option>
                </select>
                <input type="text" name="member_${memberIndex}_pincode" placeholder="Pincode" maxlength="6">
            </div>
        </fieldset>
    `;

    container.appendChild(div);

    // Wedding date toggle logic
    const marriedRadio = div.querySelector(`input[name="member_${memberIndex}_marital_status"][value="Married"]`);
    const unmarriedRadio = div.querySelector(`input[name="member_${memberIndex}_marital_status"][value="Unmarried"]`);
    const weddingDateRow = div.querySelector(`#member_${memberIndex}_wedding_date_row`);
    const weddingDate = div.querySelector(`#member_${memberIndex}_wedding_date`);

    function updateMemberWeddingDate() {
        if (marriedRadio && marriedRadio.checked) {
            weddingDateRow.style.display = '';
            weddingDate.required = true;
        } else {
            weddingDateRow.style.display = 'none';
            weddingDate.required = false;
        }
    }
    if (marriedRadio && unmarriedRadio) {
        marriedRadio.addEventListener('change', updateMemberWeddingDate);
        unmarriedRadio.addEventListener('change', updateMemberWeddingDate);
        updateMemberWeddingDate();
    }

    // states for new member
    const states = window.statesForMembers || [];
    const $stateSelect = div.querySelector(`#member_${memberIndex}_state`);
    if ($stateSelect && states.length > 0) {
        states.forEach(function(state) {
            const opt = document.createElement('option');
            opt.value = state.id;
            opt.textContent = state.name;
            $stateSelect.appendChild(opt);
        });
    }

    // Dynamic city loading
    $(div).on('change', `#member_${memberIndex}_state`, function() {
        const stateId = $(this).val();
        const $citySelect = $(div).find(`#member_${memberIndex}_city`);
        $citySelect.empty().append('<option value="">Select City</option>');
        if(stateId){
            $.ajax({
                url: "/city/",
                data: { "state_id": stateId },
                success: function(data){
                    $.each(data, function(index, city){
                        $citySelect.append('<option value="'+city.id+'">'+city.name+'</option>');
                    });
                }
            });
        }
    });
}


function toggleAddress(checkbox, index) {
    const addressDiv = document.getElementById(`address_${index}`);
    addressDiv.style.display = checkbox.checked ? 'block' : 'none';
}
