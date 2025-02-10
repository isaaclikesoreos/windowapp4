$(document).ready(function(){
    // Bind change event to the radio buttons (or select) for damage_piece.
    // If damage_piece is a radio group, use the name selector:
    $('input[name="damage_piece"]').change(function(){
        var selected = $(this).val();
        console.log("Damage piece selected:", selected); // Debug log

        // Hide both containers initially
        $('#damageSideContainer').hide();
        $('#doorSideContainer').hide();

        if(selected === 'windshield'){
            // Show the damage side container if windshield is selected
            $('#damageSideContainer').show();
        } else if (['front_door_glass', 'rear_door_glass', 'quarter_glass', 'vent_glass'].indexOf(selected) !== -1) {
            // Show door side selector for door glass options
            $('#doorSideContainer').show();
        }
    });

    // Show/hide insurance info if the user has an insurance claim
    $('input[name="has_insurance_claim"]').change(function(){
        if($(this).val() === 'True'){
            $('#insuranceInfo').show();
        } else {
            $('#insuranceInfo').hide();
        }
    });

    // Multi-step form navigation
    $('#nextStep1').click(function(){
        if($('input[name="damage_piece"]:checked').val() === 'windshield'){
            $('#step1').removeClass('active');
            $('#step2').addClass('active');
        } else {
            $('#step1').removeClass('active');
            $('#step3').addClass('active');
        }
    });

    $('#prevStep2').click(function(){
        $('#step2').removeClass('active');
        $('#step1').addClass('active');
    });
    $('#nextStep2').click(function(){
        $('#step2').removeClass('active');
        $('#step3').addClass('active');
    });
    $('#prevStep3').click(function(){
        if($('input[name="damage_piece"]:checked').val() === 'windshield'){
            $('#step3').removeClass('active');
            $('#step2').addClass('active');
        } else {
            $('#step3').removeClass('active');
            $('#step1').addClass('active');
        }
    });

    // Submit the full form via AJAX
    $('#jobEntryForm').on('submit', function(e){
        e.preventDefault();
        $.ajax({
            type: 'POST',
            url: "{% url 'quote_start' %}",
            data: $(this).serialize(),
            success: function(response){
                if(response.success){
                    alert("Job entry saved! Your ID: " + response.job_entry_id);
                } else {
                    alert("There were errors in your submission.");
                }
            },
            error: function(){
                alert("An error occurred during submission.");
            }
        });
    });
});
