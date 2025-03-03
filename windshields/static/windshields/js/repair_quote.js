$(document).ready(function(){
    // Log the VanillaCalendar object for debugging
    console.log("VanillaCalendar object:", window.VanillaCalendar);
    
    // Get the constructor from the default export
    var CalendarConstructor = window.VanillaCalendar && window.VanillaCalendar.default;
    if (!CalendarConstructor) {
        console.error("CalendarConstructor not found. Check your Vanilla Calendar file.");
    } else {
        // Instead of passing a selector, get the DOM element first.
        var calendarElement = document.querySelector("#myCalendar");
        if (!calendarElement) {
            console.error("Calendar element not found.");
        } else {
            // Create the calendar by passing the DOM element and an options object.
            var calendar = new CalendarConstructor(calendarElement, {
                // Force English language settings:
                locale: 'en',  // If supported; otherwise use lang: 'en'
                // If available, you might also set a full-month format:
                monthFormat: 'MMMM',  // e.g., "March" instead of "03" or "Mar"
                onSelect: function(data) {
                    console.log("Selected date:", data.date);
                    $('#selectedAppointment').text(data.date);
                    // (AJAX timeslot fetching remains the same)
                    $.ajax({
                        type: 'GET',
                        url: '/windshields/available-timeslots/',
                        data: { 'date': data.date },
                        success: function(response){
                            console.log("Available timeslots:", response);
                            if(response.success){
                                var html = '';
                                response.timeslots.forEach(function(slot){
                                    html += '<label class="block"><input type="radio" name="timeslot_id" value="' + slot.id + '"> ' +
                                            slot.start_time + ' - ' + slot.end_time + '</label>';
                                });
                                $('#timeslotsContainer').html(html);
                            } else {
                                $('#timeslotsContainer').html('<p>No available timeslots or error: ' + response.error + '</p>');
                            }
                        },
                        error: function(){
                            $('#timeslotsContainer').html('<p>Error fetching timeslots.</p>');
                        }
                    });
                }
            });

            
        }
    }
    
    // The rest of your scheduling JS remains the same.
    $(document).on('change', 'input[name="timeslot_id"]', function(){
        var timeslotText = $(this).closest('label').text();
        var currentText = $('#selectedAppointment').text();
        $('#selectedAppointment').text(currentText + " at " + timeslotText);
    });
    
    $('#scheduleAppointment').click(function(){
        var selectedDate = $('#selectedAppointment').text().split(" at ")[0];
        var selectedTimeslotId = $('input[name="timeslot_id"]:checked').val();
        console.log("Scheduling appointment for date:", selectedDate, "with timeslot:", selectedTimeslotId);
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
                'service_location': 'Your Service Center',
                'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            success: function(response){
                console.log("Appointment scheduled:", response);
                if(response.success){
                    alert("Appointment scheduled! Your appointment ID is: " + response.appointment_id);
                } else {
                    alert("Error scheduling appointment: " + response.error);
                }
            },
            error: function(){
                alert("An error occurred while scheduling the appointment.");
            }
        });
    });
});
