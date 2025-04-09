/**
 * VIN Decoder JavaScript for Django Application - Embedded Version
 * Integrates with the NHTSA vPIC API to decode VIN numbers
 */
document.addEventListener('DOMContentLoaded', function() {
  // Get reference to the VIN input field - adjust selector based on Django form
  const vinInput = document.getElementById('id_vin');
  const step2Element = document.getElementById('step2');
  
  if (!vinInput) {
    console.error('VIN input field not found');
    return;
  }
  
  // Create vehicle info container
  let vehicleInfoContainer = document.createElement('div');
  vehicleInfoContainer.id = 'vehicle-info-container';
  vehicleInfoContainer.className = 'vehicle-info-column hidden';
  
  // Add empty state message
  vehicleInfoContainer.innerHTML = `
    <div class="vehicle-info-empty-state">
      <div class="vehicle-icon">🚗</div>
      <h3>Vehicle Information</h3>
      <p>Enter your VIN number to see details about your vehicle</p>
    </div>
  `;
  
  // Add the vehicle info container next to step2 (not inside the form flow)
  if (step2Element) {
    // Create the wrapper for two-column layout if it doesn't exist
    let twoColWrapper = document.getElementById('step2-wrapper');
    if (!twoColWrapper) {
      // Create wrapper and insert it before step2
      twoColWrapper = document.createElement('div');
      twoColWrapper.id = 'step2-wrapper';
      twoColWrapper.className = 'step2-two-column-layout';
      step2Element.parentNode.insertBefore(twoColWrapper, step2Element);
      
      // Move step2 into the wrapper
      twoColWrapper.appendChild(step2Element);
      
      // Add the vehicle info container to the wrapper
      twoColWrapper.appendChild(vehicleInfoContainer);
    }
  } else {
    console.error('Step 2 element not found');
    return;
  }
  
  // Store the last fetched VIN to avoid duplicate requests
  let lastFetchedVin = '';
  
  // Function to check if step 2 is active
  function isStep2Active() {
    return step2Element.classList.contains('active');
  }
  
  // Function to fetch vehicle data from NHTSA API
  async function decodeVIN(vin) {
    try {
      // Show loading state
      vehicleInfoContainer.innerHTML = `
        <div class="vehicle-info-loading">
          <div class="loading-spinner"></div>
          <p>Loading vehicle information...</p>
        </div>
      `;
      
      // Show the container
      vehicleInfoContainer.classList.remove('hidden');
      
      const response = await fetch(`https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/${vin}?format=json`);
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      const data = await response.json();
      
      // Check if we got valid results
      if (data.Results && data.Results.length > 0) {
        return data.Results[0];
      } else {
        throw new Error('No vehicle data found for this VIN');
      }
    } catch (error) {
      console.error('Error decoding VIN:', error);
      
      // Show error state
      vehicleInfoContainer.innerHTML = `
        <div class="vehicle-info-error">
          <div class="error-icon">⚠️</div>
          <h3>Error</h3>
          <p>${error.message || 'Failed to decode VIN'}</p>
          <p class="small">Please check the VIN and try again</p>
        </div>
      `;
      
      return null;
    }
  }
  
  // Function to display the vehicle information
  function displayVehicleInfo(vehicleData) {
    if (!vehicleData) {
      return;
    }
    
    // Format vehicle info HTML
    const vehicleInfoHTML = `
      <div class="vehicle-info-content">
        <div class="vehicle-info-header">
          <h3>Vehicle Information</h3>
        </div>
        
        <div class="vehicle-image">
          <div class="vehicle-icon-large">🚗</div>
          <p class="image-caption">Approximate vehicle representation</p>
        </div>
        
        <div class="vehicle-primary-info">
          <h4>${vehicleData.ModelYear || ''} ${vehicleData.Make || ''} ${vehicleData.Model || ''}</h4>
          <p class="vehicle-type">${vehicleData.VehicleType || 'Vehicle'}</p>
        </div>
        
        <div class="vehicle-details">
          <div class="details-row">
            <div class="detail-box">
              <span class="detail-label">Body Style</span>
              <span class="detail-value">${vehicleData.BodyClass || 'N/A'}</span>
            </div>
            
            <div class="detail-box">
              <span class="detail-label">Engine</span>
              <span class="detail-value">${vehicleData.EngineCylinders ? vehicleData.EngineCylinders + ' cylinder' : 'N/A'}</span>
            </div>
          </div>
          
          <div class="details-row">
            <div class="detail-box">
              <span class="detail-label">Displacement</span>
              <span class="detail-value">${vehicleData.DisplacementL ? vehicleData.DisplacementL + 'L' : 'N/A'}</span>
            </div>
            
            <div class="detail-box">
              <span class="detail-label">Fuel Type</span>
              <span class="detail-value">${vehicleData.FuelTypePrimary || 'N/A'}</span>
            </div>
          </div>
          
          ${vehicleData.Trim || vehicleData.DriveType ? `
          <div class="details-row">
            ${vehicleData.Trim ? `
            <div class="detail-box">
              <span class="detail-label">Trim</span>
              <span class="detail-value">${vehicleData.Trim}</span>
            </div>
            ` : ''}
            
            ${vehicleData.DriveType ? `
            <div class="detail-box">
              <span class="detail-label">Drive Type</span>
              <span class="detail-value">${vehicleData.DriveType}</span>
            </div>
            ` : ''}
          </div>
          ` : ''}
        </div>
        
        <div class="vehicle-footer">
          <p class="vin-number">VIN: ${vehicleData.VIN || vin}</p>
          <p class="data-source">Data provided by NHTSA vPIC API</p>
        </div>
      </div>
    `;
    
    // Update the container
    vehicleInfoContainer.innerHTML = vehicleInfoHTML;
    
    // Update summary field if it exists
    const summaryVIN = document.getElementById('summaryVIN');
    if (summaryVIN) {
      // Also add vehicle info to the summary if available
      if (vehicleData.ModelYear && vehicleData.Make && vehicleData.Model) {
        summaryVIN.textContent = `${vinInput.value} (${vehicleData.ModelYear} ${vehicleData.Make} ${vehicleData.Model})`;
      } else {
        summaryVIN.textContent = vinInput.value;
      }
    }
  }
  
  // Function to check VIN and fetch data if needed
  async function checkAndFetchVIN() {
    const vin = vinInput.value.trim();
    
    // Only proceed if VIN is valid length (17 characters) and we're on step 2
    if (vin.length === 17 && isStep2Active()) {
      // Only fetch if this is a new VIN
      if (vin !== lastFetchedVin) {
        lastFetchedVin = vin;
        const vehicleData = await decodeVIN(vin);
        if (vehicleData) {
          displayVehicleInfo(vehicleData);
          vehicleInfoContainer.classList.remove('hidden');
        }
      } else {
        // If we already fetched this VIN, just show the container
        vehicleInfoContainer.classList.remove('hidden');
      }
    } else {
      vehicleInfoContainer.classList.add('hidden');
    }
  }
  
  // Add event listener for VIN input
  vinInput.addEventListener('input', function(e) {
    const vin = vinInput.value.trim();
    
    // When the VIN reaches 17 characters, automatically fetch the data
    if (vin.length === 17 && isStep2Active()) {
      checkAndFetchVIN();
    } else if (vin.length !== 17) {
      // If VIN is not 17 characters, hide the panel
      vehicleInfoContainer.classList.add('hidden');
      // Reset last fetched VIN if user is modifying the VIN
      if (vin.length < 17) {
        lastFetchedVin = '';
      }
    }
  });

  // Also check when the field loses focus (as a fallback)
  vinInput.addEventListener('blur', function() {
    checkAndFetchVIN();
  });
  
  // Listen for step changes (assuming you have navigation buttons)
  const nextStep1Button = document.getElementById('nextStep1');
  const prevStep2Button = document.getElementById('prevStep2');
  
  if (nextStep1Button) {
    nextStep1Button.addEventListener('click', function() {
      // Check if step 2 is now active and VIN length is 17
      setTimeout(() => {
        checkAndFetchVIN();
      }, 100); // Small delay to ensure class changes have been processed
    });
  }
  
  if (prevStep2Button) {
    prevStep2Button.addEventListener('click', function() {
      // Hide vehicle info when going back to step 1
      vehicleInfoContainer.classList.add('hidden');
    });
  }
  
  // Add observer to monitor step visibility
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
        checkAndFetchVIN();
      }
    });
  });
  
  observer.observe(step2Element, { attributes: true });
  
  // Initial check in case the page loads with a pre-filled VIN
  setTimeout(() => {
    checkAndFetchVIN();
  }, 500);
});