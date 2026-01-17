# Lead Recovery Engine - ROI Calculator Specification

## Interactive ROI Calculator Tool

### Purpose
Client-facing tool that calculates projected ROI based on their specific lead database and business metrics.

### Input Parameters

#### Client Business Metrics
```javascript
// Primary Database Information
const clientInputs = {
  totalLeads: {
    type: "number",
    label: "Total Leads in CRM Database",
    placeholder: "25000",
    min: 1000,
    max: 1000000,
    required: true
  },

  currentConversionRate: {
    type: "percentage",
    label: "Current Lead Conversion Rate (%)",
    placeholder: "1.2",
    min: 0.1,
    max: 10.0,
    default: 1.2,
    required: true
  },

  averageDealValue: {
    type: "currency",
    label: "Average Deal Value ($)",
    placeholder: "350000",
    min: 1000,
    max: 10000000,
    required: true
  },

  monthlyLeadAcquisitionCost: {
    type: "currency",
    label: "Monthly New Lead Acquisition Cost ($)",
    placeholder: "15000",
    min: 1000,
    max: 500000,
    required: true
  },

  manualOutreachHoursPerWeek: {
    type: "number",
    label: "Hours Spent on Manual Follow-up (per week)",
    placeholder: "12",
    min: 1,
    max: 80,
    required: true
  },

  averageHourlyCost: {
    type: "currency",
    label: "Average Agent Hourly Cost ($)",
    placeholder: "75",
    min: 15,
    max: 200,
    default: 75,
    required: false
  }
}
```

#### Lead Database Analysis
```javascript
const leadAnalysis = {
  dormancyThreshold: {
    type: "select",
    label: "Consider leads dormant after:",
    options: [
      {value: 7, label: "7 days"},
      {value: 14, label: "14 days"},
      {value: 30, label: "30 days (default)"},
      {value: 60, label: "60 days"},
      {value: 90, label: "90 days"}
    ],
    default: 30
  },

  estimatedDormantPercentage: {
    type: "percentage",
    label: "Estimated % of Dormant Leads",
    placeholder: "70",
    min: 30,
    max: 95,
    default: 70,
    help: "Industry average: 60-80%"
  }
}
```

### Calculation Engine

#### Core ROI Calculations
```javascript
class LeadRecoveryROICalculator {

  calculateBaseline(inputs) {
    const totalLeads = inputs.totalLeads;
    const conversionRate = inputs.currentConversionRate / 100;
    const avgDealValue = inputs.averageDealValue;
    const dormantPercentage = inputs.estimatedDormantPercentage / 100;

    return {
      currentMonthlyDeals: Math.floor((totalLeads * conversionRate) / 12),
      currentAnnualRevenue: totalLeads * conversionRate * avgDealValue,
      dormantLeads: Math.floor(totalLeads * dormantPercentage),
      lostOpportunityValue: Math.floor(totalLeads * dormantPercentage * conversionRate * avgDealValue)
    };
  }

  calculateRecoveryScenarios(inputs, baseline) {
    const scenarios = {
      conservative: {
        reactivationRate: 0.30,
        newConversionRate: 0.03,
        description: "Conservative: 30% reactivation, 3% convert"
      },
      moderate: {
        reactivationRate: 0.45,
        newConversionRate: 0.05,
        description: "Moderate: 45% reactivation, 5% convert"
      },
      aggressive: {
        reactivationRate: 0.60,
        newConversionRate: 0.08,
        description: "Aggressive: 60% reactivation, 8% convert"
      }
    };

    const results = {};

    Object.keys(scenarios).forEach(scenario => {
      const config = scenarios[scenario];
      const reactivatedLeads = Math.floor(baseline.dormantLeads * config.reactivationRate);
      const newDeals = Math.floor(reactivatedLeads * config.newConversionRate);
      const additionalRevenue = newDeals * inputs.averageDealValue;

      results[scenario] = {
        ...config,
        reactivatedLeads,
        newDeals,
        additionalRevenue,
        totalRevenue: baseline.currentAnnualRevenue + additionalRevenue
      };
    });

    return results;
  }

  calculateCostSavings(inputs) {
    const hourlyReduction = inputs.manualOutreachHoursPerWeek * 0.7; // 70% time savings
    const weeklySavings = hourlyReduction * inputs.averageHourlyCost;
    const annualLaborSavings = weeklySavings * 52;

    const leadAcquisitionReduction = inputs.monthlyLeadAcquisitionCost * 0.25; // 25% reduction
    const annualAcquisitionSavings = leadAcquisitionReduction * 12;

    return {
      annualLaborSavings,
      annualAcquisitionSavings,
      totalAnnualSavings: annualLaborSavings + annualAcquisitionSavings
    };
  }

  calculateInvestmentTiers() {
    return {
      foundation: {
        name: "Foundation",
        price: 100000,
        description: "10k-50k contacts, standard integrations",
        features: ["Core behavioral triggers", "Standard CRM integration", "Basic analytics"]
      },
      professional: {
        name: "Professional",
        price: 150000,
        description: "50k-150k contacts, advanced orchestration",
        features: ["Multi-channel orchestration", "Strategic consultation", "Dedicated success manager"]
      },
      enterprise: {
        name: "Enterprise",
        price: 225000,
        description: "150k+ contacts, white-glove implementation",
        features: ["Custom implementation", "Weekly reviews", "Priority support"]
      }
    };
  }

  calculateROI(additionalRevenue, costSavings, investment) {
    const totalBenefit = additionalRevenue + costSavings;
    const roi = ((totalBenefit - investment) / investment) * 100;
    const paybackMonths = (investment / (totalBenefit / 12));

    return {
      totalBenefit,
      netBenefit: totalBenefit - investment,
      roiPercentage: roi,
      paybackMonths: Math.ceil(paybackMonths)
    };
  }
}
```

### User Interface Specification

#### Step 1: Business Information Input
```html
<div class="roi-calculator-step" id="step-1">
  <h2>Your Business Metrics</h2>
  <p>Enter your current lead database and performance metrics to calculate your ROI potential.</p>

  <div class="input-grid">
    <div class="input-group">
      <label>Total Leads in CRM Database</label>
      <input type="number" id="totalLeads" placeholder="25,000" />
      <span class="help-text">Include all leads from the past 2 years</span>
    </div>

    <div class="input-group">
      <label>Current Conversion Rate (%)</label>
      <input type="number" id="conversionRate" placeholder="1.2" step="0.1" />
      <span class="help-text">Industry average: 0.4-1.2%</span>
    </div>

    <div class="input-group">
      <label>Average Deal Value ($)</label>
      <input type="number" id="dealValue" placeholder="350,000" />
      <span class="help-text">Your typical commission or sale value</span>
    </div>

    <div class="input-group">
      <label>Monthly Lead Acquisition Cost ($)</label>
      <input type="number" id="acquisitionCost" placeholder="15,000" />
      <span class="help-text">Total spent on new lead generation</span>
    </div>
  </div>

  <button class="calculate-btn" onclick="calculateROI()">Calculate My ROI Potential</button>
</div>
```

#### Step 2: Results Dashboard
```html
<div class="results-dashboard" id="results">
  <div class="current-state">
    <h3>Your Current State</h3>
    <div class="metric-grid">
      <div class="metric">
        <span class="value" id="currentRevenue">$8.4M</span>
        <span class="label">Annual Revenue</span>
      </div>
      <div class="metric">
        <span class="value" id="dormantLeads">17,500</span>
        <span class="label">Dormant Leads</span>
      </div>
      <div class="metric">
        <span class="value" id="lostValue">$3.7M</span>
        <span class="label">Lost Opportunity</span>
      </div>
    </div>
  </div>

  <div class="recovery-scenarios">
    <h3>Lead Recovery Projections</h3>
    <div class="scenario-tabs">
      <button class="tab active" data-scenario="moderate">Moderate</button>
      <button class="tab" data-scenario="conservative">Conservative</button>
      <button class="tab" data-scenario="aggressive">Aggressive</button>
    </div>

    <div class="scenario-results" id="moderate-results">
      <div class="recovery-metrics">
        <div class="metric">
          <span class="value">7,875</span>
          <span class="label">Leads Reactivated</span>
        </div>
        <div class="metric">
          <span class="value">394</span>
          <span class="label">New Deals</span>
        </div>
        <div class="metric">
          <span class="value">$1.38M</span>
          <span class="label">Additional Revenue</span>
        </div>
      </div>
    </div>
  </div>

  <div class="roi-summary">
    <h3>ROI Analysis</h3>
    <div class="investment-tiers">
      <div class="tier recommended" data-tier="professional">
        <div class="tier-header">
          <span class="tier-name">Professional</span>
          <span class="tier-price">$150,000</span>
        </div>
        <div class="roi-metrics">
          <div class="roi-metric">
            <span class="value">247%</span>
            <span class="label">24-Month ROI</span>
          </div>
          <div class="roi-metric">
            <span class="value">8 months</span>
            <span class="label">Payback Period</span>
          </div>
        </div>
        <div class="benefit-breakdown">
          <div class="benefit">
            <span class="amount">$1,380,000</span>
            <span class="desc">Additional Revenue (24 months)</span>
          </div>
          <div class="benefit">
            <span class="amount">$156,000</span>
            <span class="desc">Cost Savings (24 months)</span>
          </div>
          <div class="benefit">
            <span class="amount">$521,000</span>
            <span class="desc">Net Profit (24 months)</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="action-section">
    <h3>Next Steps</h3>
    <p>Ready to unlock your lead recovery potential?</p>
    <button class="cta-btn">Schedule Technical Discovery Call</button>
    <button class="secondary-btn">Download Full ROI Report</button>
  </div>
</div>
```

### Visual Design Elements

#### Color Scheme (Cinematic UI v4.0)
```css
:root {
  --primary-color: #6366F1;      /* Indigo - actions */
  --success-color: #10B981;      /* Emerald - gains */
  --warning-color: #F59E0B;      /* Amber - attention */
  --danger-color: #EF4444;       /* Red - losses */
  --background-dark: #05070A;    /* Deep background */
  --card-glass: rgba(13, 17, 23, 0.8); /* Glassmorphic cards */
}

.metric {
  background: var(--card-glass);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  padding: 24px;
  transition: all 0.3s ease;
}

.metric:hover {
  transform: translateY(-5px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 15px 50px rgba(99, 102, 241, 0.15);
}
```

#### Interactive Charts
```javascript
// Recovery projection chart using Chart.js
const recoveryChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['Current', '3 Months', '6 Months', '12 Months', '24 Months'],
    datasets: [{
      label: 'Cumulative Revenue Recovery',
      data: [0, 345000, 690000, 1380000, 2760000],
      borderColor: '#10B981',
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return '$' + (value / 1000000).toFixed(1) + 'M';
          }
        }
      }
    }
  }
});
```

### Integration & Deployment

#### Lead Qualification Integration
```javascript
// Capture lead information for follow-up
function captureROIResults() {
  const results = {
    companyName: document.getElementById('companyName').value,
    contactName: document.getElementById('contactName').value,
    email: document.getElementById('email').value,
    phone: document.getElementById('phone').value,
    calculatorInputs: getCalculatorInputs(),
    projectedROI: getROIResults(),
    selectedTier: getSelectedTier(),
    timestamp: new Date().toISOString()
  };

  // Send to CRM for follow-up
  fetch('/api/v1/roi-calculator/submit', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(results)
  });

  // Trigger immediate notification for high-value prospects
  if (results.projectedROI.totalBenefit > 1000000) {
    sendHighValueAlert(results);
  }
}
```

#### Analytics Tracking
```javascript
// Track calculator usage and conversion points
function trackCalculatorEvent(eventType, data) {
  gtag('event', 'roi_calculator_interaction', {
    event_category: 'Lead Generation',
    event_label: eventType,
    value: data.projectedInvestment || 0,
    custom_parameters: {
      lead_database_size: data.totalLeads,
      projected_roi: data.roiPercentage,
      payback_months: data.paybackMonths
    }
  });
}
```

### Professional Output Features

#### PDF Report Generation
- Executive summary with key metrics
- Detailed ROI breakdown by scenario
- Implementation timeline and milestones
- Contact information and next steps
- Professional branding and formatting

#### Email Follow-up Automation
- Immediate results summary email
- 7-day follow-up with additional resources
- 30-day case study sharing
- Quarterly industry benchmark updates

The ROI calculator serves as both a lead qualification tool and credibility demonstration, providing prospects with personalized business impact projections while capturing valuable lead information for sales follow-up.