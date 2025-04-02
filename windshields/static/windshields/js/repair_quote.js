$(document).ready(function(){
    // Log initialization
    console.log("Document ready, initializing flatpickr...");
    
    // Initialize the calendar
    initializeCalendar();
    
    // The scheduleAppointment click handler
    $('#scheduleAppointment').click(function(){
        var selectedDate = $('#selectedAppointment').text().split(" at ")[0];
        var selectedTimeslotId = $('input[name="timeslot_id"]:checked').val();
        var serviceLocation = $('#serviceLocation').val();
        
        console.log("Scheduling appointment for date:", selectedDate, 
                   "with timeslot:", selectedTimeslotId,
                   "at location:", serviceLocation);
        
        if(!selectedDate || !selectedTimeslotId){
            alert("Please select a date and a timeslot.");
            return;
        }
        
        $.ajax({
            type: 'POST',
            url: '/windshields/schedule-appointment/',
            data: {
                'date': selectedDate,
                'timeslot_ids[]': [selectedTimeslotId],
                'service_location': serviceLocation,
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response){
                console.log("Appointment scheduled:", response);
                if(response.success){
                    alert("Appointment scheduled successfully! Your appointment ID is: " + response.appointment_id);
                    // Optionally redirect to a confirmation page
                } else {
                    alert("Error scheduling appointment: " + response.error);
                }
            },
            error: function(){
                alert("An error occurred while scheduling the appointment.");
            }
        });
    });
    
    // Handlers for switching between insurance and customer pay quotes
    $('#switchToCustomerQuote').click(function(){
        // Handled in the template-specific script
    });
    
    $('#proceedWithInsurance').click(function(){
        // Handled in the template-specific script
    });
    
    // Handle timeslot selection
    $(document).on('change', 'input[name="timeslot_id"]', function(){
        var timeslotText = $(this).closest('label').text().trim();
        var currentText = $('#selectedAppointment').text();
        if(currentText.indexOf(" at ") > -1) {
            currentText = currentText.split(" at ")[0];
        }
        $('#selectedAppointment').text(currentText + " at " + timeslotText);
    });
});

function initializeCalendar() {
    var calendarElement = document.getElementById('myCalendar');
    if (!calendarElement) {
        console.error("Calendar element not found!");
        return;
    }
    
    console.log("Found calendar element, initializing flatpickr...");
    
    // Get today's date for min date
    var today = new Date();
    var todayFormatted = today.toISOString().split('T')[0];
    
    // Initialize flatpickr
    var calendar = flatpickr(calendarElement, {
        inline: true,
        minDate: todayFormatted,
        dateFormat: "Y-m-d",
        onChange: function(selectedDates, dateStr) {
            console.log("Selected date:", dateStr);
            $('#selectedAppointment').text(dateStr);
            
            // Fetch available timeslots for the selected date
            $.ajax({
                type: 'GET',
                url: '/windshields/available-timeslots/',
                data: { 'date': dateStr },
                success: function(response){
                    console.log("Available timeslots response:", response);
                    if(response.success){
                        var html = '<div class="grid grid-cols-2 gap-2">';
                        if(response.timeslots && response.timeslots.length > 0) {
                            // Initial limit of slots to show
                            const initialLimit = 8;
                            const hasMoreSlots = response.timeslots.length > initialLimit;
                            
                            // Show first 8 slots
                            for(let i = 0; i < Math.min(initialLimit, response.timeslots.length); i++) {
                                const slot = response.timeslots[i];
                                html += '<label class="block p-2 border rounded hover:bg-gray-100">' +
                                        '<input type="radio" name="timeslot_id" value="' + slot.id + '"> ' +
                                        slot.start_time + ' - ' + slot.end_time + '</label>';
                            }
                            
                            // If there are more slots, add a container for them and a "See More" button
                            if(hasMoreSlots) {
                                html += '</div>'; // Close the initial grid
                                
                                html += '<div class="mt-2">' +
                                        '<button id="seeMoreSlots" class="text-blue-600 hover:underline">See More Appointments</button>' +
                                        '</div>';
                                
                                html += '<div id="moreTimeslots" class="hidden mt-2 grid grid-cols-2 gap-2">';
                                
                                // Add the remaining slots to the hidden container
                                for(let i = initialLimit; i < response.timeslots.length; i++) {
                                    const slot = response.timeslots[i];
                                    html += '<label class="block p-2 border rounded hover:bg-gray-100">' +
                                            '<input type="radio" name="timeslot_id" value="' + slot.id + '"> ' +
                                            slot.start_time + ' - ' + slot.end_time + '</label>';
                                }
                                
                                html += '</div>'; // Close the "more" container
                            } else {
                                html += '</div>'; // Close the grid
                            }
                            
                            $('#timeslotsContainer').html(html);
                            
                            // Add click handler for the "See More" button
                            $('#seeMoreSlots').on('click', function() {
                                $('#moreTimeslots').toggleClass('hidden');
                                $(this).text(
                                    $('#moreTimeslots').hasClass('hidden') ? 
                                    'See More Appointments' : 
                                    'Hide Additional Appointments'
                                );
                            });
                        } else {
                            html += '<p class="col-span-2 text-red-500">No available timeslots for this date.</p></div>';
                            $('#timeslotsContainer').html(html);
                        }
                    } else {
                        $('#timeslotsContainer').html('<p class="text-red-500">Error fetching timeslots: ' + (response.error || "Unknown error") + '</p>');
                    }
                },
                error: function(xhr, status, error){
                    console.error("AJAX error:", status, error);
                    $('#timeslotsContainer').html('<p class="text-red-500">Error contacting the server. Please try again.</p>');
                }
            });
        }
    });
    
    console.log("Flatpickr initialized:", calendar);
    return calendar;
}