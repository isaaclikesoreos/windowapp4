$(document).ready(function(){
    // Bind change event for damage_piece
    $('#id_damage_piece').change(function(){
        var selected = $(this).val();
        console.log("Damage piece selected:", selected);
        $('#doorSideContainer').addClass('hidden');
        $('#repairOptionContainer').addClass('hidden');
        if(selected === 'windshield'){
            $('#repairOptionContainer').removeClass('hidden');
        } else if (['front_door_glass', 'rear_door_glass', 'quarter_glass', 'vent_glass'].indexOf(selected) !== -1) {
            $('#doorSideContainer').removeClass('hidden');
        }
    });

    // Toggle insurance details based on has_insurance_claim selection
    $('input[name="has_insurance_claim"]').change(function(){
        var claimVal = $(this).val();
        console.log("Has insurance claim:", claimVal);
        if(claimVal === 'True'){
            $('#insuranceDetailsContainer').removeClass('hidden');
        } else {
            $('#insuranceDetailsContainer').addClass('hidden');
        }
    });
    
    // Navigation: Move from Step 1 to Step 2
    $('#nextStep1').click(function(){
        // Validate required fields in step 1
        var damageType = $('#id_damage_piece').val();
        var causeOfDamage = $('#id_cause_of_damage').val();
        
        // Validate windshield repair option if windshield is selected
        if(damageType === 'windshield') {
            var isRepairable = $('input[name="is_repairable"]:checked').val();
            if(isRepairable === undefined) {
                alert("Please indicate whether the windshield is repairable.");
                return;
            }
        }
        
        // Validate side selection if a door/quarter/vent glass is selected
        if(['front_door_glass', 'rear_door_glass', 'quarter_glass', 'vent_glass'].indexOf(damageType) !== -1) {
            var damageSide = $('input[name="damage_side"]:checked').val();
            if(!damageSide) {
                alert("Please select which side (driver or passenger).");
                return;
            }
        }
        
        if(!damageType || !causeOfDamage) {
            alert("Please complete all required fields before proceeding.");
            return;
        }
        
        $('#step1').removeClass('active');
        $('#step2').addClass('active');
    });
    
    // Navigation: Back from Step 2 to Step 1
    $('#prevStep2').click(function(){
        $('#step2').removeClass('active');
        $('#step1').addClass('active');
    });
    
    // Transition from Step 2 to Step 3
    $('#nextStep2').click(function(){
        // Validate required fields in step 2
        var firstName = $('#id_first_name').val().trim();
        var lastName = $('#id_last_name').val().trim();
        var phone = $('#id_phone').val().trim();
        var vin = $('#id_vin').val().trim();
        
        if(!firstName || !lastName || !phone || !vin) {
            alert("Please complete all required fields before proceeding.");
            return;
        }
        
        // Validate insurance information if customer selected "has insurance"
        var hasInsurance = $('input[name="has_insurance_claim"]:checked').val() === 'True';
        if(hasInsurance) {
            var insuranceName = $('#id_insurance_name').val().trim();
            var policyNumber = $('#id_policy_number').val().trim();
            
            if(!insuranceName || !policyNumber) {
                alert("Please provide your insurance information before proceeding.");
                return;
            }
        }
        
        $('#step2').removeClass('active');
        $('#step3').addClass('active');
        generateQuoteOptions();
        populateCustomerSummary();
    });
    
    // Confirm button in Step 3: start red and then change to green upon confirmation
    $('#confirmStep3').css("background-color", "red");
    $('#confirmStep3').click(function(){
        if($('input[name="quote_type"]:checked').length > 0){
            console.log("Quote type confirmed.");
            $(this).prop('disabled', true).css("background-color", "green");
            $('#nextStep3').removeClass('hidden');  // Reveal the submit button
        } else {
            alert("Please select a quote type before confirming.");
        }
    });
    
    // Edit button in Step 3
    $('#editStep3').click(function(){
        $('#step3').removeClass('active');
        $('#step2').addClass('active');
    });
    
    // Final submission: Log to console when submit button is pressed
    $('#jobEntryForm').on('submit', function(e){
        e.preventDefault();
        console.log("Submit button pressed. Sending data to backend...");
        var postUrl = $("#jobEntryForm").data("url");
        $.ajax({
            type: 'POST',
            url: postUrl,
            data: $(this).serialize(),
            success: function(response){
                console.log("Backend response received:", response);
                if(response.success){
                    if(response.redirect_url){
                        console.log("Redirecting to: " + response.redirect_url);
                        window.location.href = response.redirect_url;
                    } else {
                        alert("Job entry saved! Your ID: " + response.job_entry_id);
                    }
                } else {
                    alert("There were errors in your submission.");
                }
            },
            error: function(){
                alert("An error occurred during submission.");
            }
        });
    });
    
    
    // Functions to generate quote options and populate summary
    function generateQuoteOptions() {
        var damagePiece = $('#id_damage_piece').val();
        var hasInsurance = $('input[name="has_insurance_claim"]:checked').val() === 'True';
        var optionHtml = '';

        if (damagePiece === 'windshield') {
            var isRepairable = $('input[name="is_repairable"]:checked').val() === 'True';
            if (hasInsurance) {
                if (isRepairable) {
                    optionHtml += '<label class="inline-block mr-4"><input type="radio" name="quote_type" value="windshield_repair_claim"> I would like to proceed with a <strong>windshield repair claim</strong></label>';
                    optionHtml += '<label class="inline-block mr-4"><input type="radio" name="quote_type" value="windshield_replacement_claim"> I would like to proceed with a <strong>windshield replacement claim</strong></label>';
                } else {
                    optionHtml += '<label class="inline-block mr-4"><input type="radio" name="quote_type" value="windshield_replacement_claim"> I would like to proceed with a <strong>windshield replacement claim</strong></label>';
                }
            } else {
                if (isRepairable) {
                    optionHtml += '<label class="inline-block mr-4"><input type="radio" name="quote_type" value="windshield_repair_quote"> I would like to proceed with a <strong>windshield repair</strong> quote</label>';
                    optionHtml += '<label class="inline-block mr-4"><input type="radio" name="quote_type" value="windshield_replacement_quote"> I would like to proceed with a <strong>windshield replacement</strong> quote</label>';
                } else {
                    optionHtml += '<label class="inline-block mr-4"><input type="radio" name="quote_type" value="windshield_replacement_quote"> I would like to proceed with a <strong>windshield replacement</strong> quote</label>';
                }
            }
        } else {
            var glassLabel = $('#id_damage_piece option:selected').text();
            var sideLabel = '';
            if (damagePiece !== 'back_glass') {
                sideLabel = $('input[name="damage_side"]:checked').val();
                if (sideLabel === 'driver') {
                    sideLabel = 'Driver';
                } else if (sideLabel === 'passenger') {
                    sideLabel = 'Passenger';
                }
            }
            var text;
            if (hasInsurance) {
                text = 'I would like to proceed with a ';
                if (sideLabel) {
                    text += sideLabel + ' ';
                }
                text += glassLabel.toLowerCase() + ' replacement claim';
            } else {
                text = 'I would like to proceed with a ';
                if (sideLabel) {
                    text += sideLabel + ' ';
                }
                text += glassLabel.toLowerCase() + ' replacement quote';
            }
            optionHtml += '<label class="inline-block mr-4"><input type="radio" name="quote_type" value="non_windshield"> ' + text + '</label>';
        }
        $('#quoteOptions').html(optionHtml);
    }
    
    function populateCustomerSummary() {
        $('#summaryFirstName').text($('#id_first_name').val());
        $('#summaryLastName').text($('#id_last_name').val());
        $('#summaryPhone').text($('#id_phone').val());
        $('#summaryEmail').text($('#id_email').val());
        $('#summaryVIN').text($('#id_vin').val());
        var hasInsurance = $('input[name="has_insurance_claim"]:checked').val() === 'True';
        if(hasInsurance) {
            $('#summaryInsurance').removeClass('hidden');
            $('#summaryInsuranceName').text($('#id_insurance_name').val());
            $('#summaryPolicyNumber').text($('#id_policy_number').val());
            $('#summaryClaimNumber').text($('#id_claim_number').val());
            $('#summaryReferralNumber').text($('#id_referral_number').val());
        } else {
            $('#summaryInsurance').addClass('hidden');
        }
    }
});