from strands import tool
from typing import Optional, List, Dict, Any
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@tool
def bva_calculator(params: dict) -> dict:
    """
    Calculates business value analysis (BVA) metrics based on operational and financial parameters.
    
    This function performs comprehensive business value calculations including cost savings,
    revenue growth, customer churn reduction, and ROI analysis. It returns detailed breakdowns
    of each component with step-by-step calculation explanations.
    
    IMPORTANT: Time savings from AI Agents are used in both Cost_savings and Revenue_growth 
    calculations. To avoid double-counting benefits, consider using either Cost_savings OR 
    Revenue_growth components, but not both simultaneously. Choose based on your business model:
    - Use Cost_savings if the primary benefit is reducing labor costs
    - Use Revenue_growth if the primary benefit is generating additional revenue from freed-up time
    
    Customer_churn_reduction benefits are independent of time savings and can be safely 
    combined with either Cost_savings or Revenue_growth without double-counting concerns.
    
    Input: dict with global parameters and component keys for different value categories
    
    Global parameters:
    - analysis_period_months: Duration of analysis in months (default: 12)
    - baseline_date: Starting date for analysis (optional)
    - currency: Currency code for calculations (default: 'USD')
    - questions_per_month: Number of questions processed per month
    - minutes_per_question_without_ai: Time spent per question without AI Agent (float, in minutes, default: 10)
    - minutes_per_question_with_ai: Time spent per question with AI Agent (float, in minutes, default: 2)
    - percent_questions_that_save_time: Percentage of questions where AI actually saves time (float, default: 80)
    - ai_agent_cost_per_month: Total monthly cost of AI Agent (float, includes Bedrock, AgentCore, etc.)
    
    Cost_savings parameters:
    - labor_cost_per_hour: Hourly labor cost rate (float, default: 100)
    

    Revenue_growth parameters:
    - percent_time_to_new_projects: Percentage of saved time allocated to new revenue-generating projects (float, default: 60)
    - revenue_per_employee_per_hour: Revenue generated per employee per hour (float, default: 150)
    
    Customer_churn_reduction parameters:
    - total_customer_count: Total number of customers
    - customer_churn_before_ai: Monthly customer churn rate before AI (float, default: 1.0%)
    - customer_churn_after_ai: Monthly customer churn rate after AI (float, default: 0.5%)
    - average_monthly_revenue_per_customer: Average monthly revenue per customer (float, default: 100)
    - cost_of_acquiring_new_customer: Cost to acquire new customer (calculated as 20% of annual revenue per customer)
    
    # Risk_mitigation parameters: (COMMENTED OUT FOR NOW)
    # - compliance_cost_avoidance: Monthly compliance costs avoided
    # - security_incident_cost_avoidance: Potential security incident costs avoided
    # - downtime_cost_avoidance: Monthly downtime costs avoided
    # - reputation_risk_value: Estimated monthly value of reputation protection
    # - percent_risk_confidence: Confidence level in risk mitigation (default: 60%)
    
    Implementation_costs parameters:
    - one_time_implementation_cost: One-time implementation and setup cost (float, default: 100000)
    - one_time_training_cost: One-time training and change management cost (float, default: 20000)
    
    Output: dict with calculated business value metrics for each component, total ROI,
    payback period, and detailed step-by-step calculation explanations.
    """
    results = {}
    
    # ========================================
    # STEP 1: Extract and validate global parameters
    # ========================================
    try:
        # Basic analysis parameters
        analysis_period_months = params.get('analysis_period_months', 12)
        baseline_date = params.get('baseline_date', 'Not specified')
        currency = params.get('currency', 'USD')
        
        # Core operational parameters (required)
        questions_per_month = params.get('questions_per_month')
        ai_agent_cost_per_month = params.get('ai_agent_cost_per_month')
        
        # Time efficiency parameters (with sensible defaults)
        minutes_per_question_without_ai = params.get('minutes_per_question_without_ai', 10)
        minutes_per_question_with_ai = params.get('minutes_per_question_with_ai', 2)
        percent_questions_that_save_time = params.get('percent_questions_that_save_time', 80) / 100
        
    except Exception as e:
        error_msg = f'Invalid global parameters: {str(e)}'
        logger.exception(error_msg)
        return {'error': error_msg}
    
    # Validate required parameters
    if questions_per_month is None:
        error_msg = 'Missing required global parameter: questions_per_month'
        logger.error(error_msg)
        return {'error': error_msg}
    if ai_agent_cost_per_month is None:
        error_msg = 'Missing required global parameter: ai_agent_cost_per_month'
        logger.error(error_msg)
        return {'error': error_msg}
    
    # Store global parameters in results
    results['global_parameters'] = {
        'analysis_period_months': analysis_period_months,
        'baseline_date': baseline_date,
        'currency': currency,
        'questions_per_month': questions_per_month,
        'minutes_per_question_without_ai': minutes_per_question_without_ai,
        'minutes_per_question_with_ai': minutes_per_question_with_ai,
        'percent_questions_that_save_time': percent_questions_that_save_time * 100,
        'ai_agent_cost_per_month': ai_agent_cost_per_month
    }
    
    # ========================================
    # STEP 2: Cost Savings Calculation
    # Calculates labor cost reductions from AI-driven time savings
    # ========================================
    if 'cost_savings' in params:
        try:
            cost_params = params['cost_savings']
            
            # Extract labor cost parameter
            labor_cost_per_hour = cost_params.get('labor_cost_per_hour', 100)
            
            # Calculate realistic time savings (not all questions will benefit from AI)
            effective_questions_saving_time = questions_per_month * percent_questions_that_save_time
            questions_not_saving_time = questions_per_month - effective_questions_saving_time
            
            # Time savings per question (in minutes)
            time_saved_per_question = minutes_per_question_without_ai - minutes_per_question_with_ai
            
            # Convert to monthly hours for cost calculations
            total_time_without_ai_hours = (questions_per_month * minutes_per_question_without_ai) / 60
            
            # Mixed scenario: some questions save time (use AI time), others don't (use original time)
            total_time_with_ai_hours = ((effective_questions_saving_time * minutes_per_question_with_ai) + 
                                      (questions_not_saving_time * minutes_per_question_without_ai)) / 60
            
            # Total hours saved per month
            total_time_saved_hours = (effective_questions_saving_time * time_saved_per_question) / 60
            
            # Calculate labor costs in different scenarios
            monthly_labor_cost_without_ai = total_time_without_ai_hours * labor_cost_per_hour
            monthly_labor_cost_with_ai = total_time_with_ai_hours * labor_cost_per_hour
            monthly_labor_savings = total_time_saved_hours * labor_cost_per_hour
            
            # Net savings = labor savings minus AI agent costs
            monthly_net_savings = monthly_labor_savings - ai_agent_cost_per_month
            
            # Project savings over the full analysis period
            total_labor_savings_period = monthly_labor_savings * analysis_period_months
            total_ai_cost_period = ai_agent_cost_per_month * analysis_period_months
            total_net_savings_period = monthly_net_savings * analysis_period_months
            
            # Create step-by-step calculation explanations for transparency
            explanations = [
                f"Step 1: Questions that actually save time = {effective_questions_saving_time:,.0f} questions ({questions_per_month:,} total × {percent_questions_that_save_time:.1%} success rate)",
                f"Step 2: Time saved per successful question = {time_saved_per_question:.1f} minutes ({minutes_per_question_without_ai:.1f} min without AI - {minutes_per_question_with_ai:.1f} min with AI)",
                f"Step 3: Total monthly time saved = {total_time_saved_hours:,.1f} hours ({effective_questions_saving_time:,.0f} questions × {time_saved_per_question:.1f} min ÷ 60)",
                f"Step 4: Monthly labor cost without AI = ${monthly_labor_cost_without_ai:,.2f} ({total_time_without_ai_hours:,.1f} hours × ${labor_cost_per_hour}/hour)",
                f"Step 5: Monthly labor cost with AI = ${monthly_labor_cost_with_ai:,.2f} ({total_time_with_ai_hours:,.1f} hours × ${labor_cost_per_hour}/hour)",
                f"Step 6: Monthly labor savings = ${monthly_labor_savings:,.2f} ({total_time_saved_hours:,.1f} hours × ${labor_cost_per_hour}/hour)",
                f"Step 7: Net monthly savings = ${monthly_net_savings:,.2f} (${monthly_labor_savings:,.2f} labor savings - ${ai_agent_cost_per_month:,.2f} AI costs)",
                f"Step 8: Total net savings over {analysis_period_months} months = ${total_net_savings_period:,.2f}"
            ]
            
            results['cost_savings'] = {
                'questions_per_month': questions_per_month,
                'effective_questions_saving_time': effective_questions_saving_time,
                'percent_questions_that_save_time': percent_questions_that_save_time * 100,
                'time_saved_per_question_minutes': time_saved_per_question,
                'total_time_saved_hours_per_month': total_time_saved_hours,
                'monthly_labor_cost_without_ai': monthly_labor_cost_without_ai,
                'monthly_labor_cost_with_ai': monthly_labor_cost_with_ai,
                'monthly_labor_savings': monthly_labor_savings,
                'ai_agent_cost_per_month': ai_agent_cost_per_month,
                'monthly_net_savings': monthly_net_savings,
                'total_labor_savings_period': total_labor_savings_period,
                'total_ai_cost_period': total_ai_cost_period,
                'total_net_savings_period': total_net_savings_period,
                'calculation_explanations': explanations
            }
        except Exception as e:
            error_msg = f'Error calculating cost savings: {str(e)}'
            logger.exception(error_msg)
            return {'error': error_msg}
    

    # ========================================
    # STEP 3: Revenue Growth Calculation
    # Calculates additional revenue from time allocated to new projects
    # ========================================
    if 'revenue_growth' in params:
        try:
            revenue_params = params['revenue_growth']
            
            # Extract revenue growth parameters
            percent_time_to_new_projects = revenue_params.get('percent_time_to_new_projects', 60) / 100
            revenue_per_employee_per_hour = revenue_params.get('revenue_per_employee_per_hour', 150)
            
            # Get time savings (reuse from cost_savings if available, otherwise calculate)
            if 'cost_savings' in results:
                total_time_saved_hours = results['cost_savings']['total_time_saved_hours_per_month']
            else:
                # Calculate time savings independently
                effective_questions_saving_time = questions_per_month * percent_questions_that_save_time
                time_saved_per_question = minutes_per_question_without_ai - minutes_per_question_with_ai
                total_time_saved_hours = (effective_questions_saving_time * time_saved_per_question) / 60
            
            # Calculate revenue from reallocated time
            time_allocated_to_new_projects = total_time_saved_hours * percent_time_to_new_projects
            monthly_additional_revenue = time_allocated_to_new_projects * revenue_per_employee_per_hour
            total_revenue_growth_period = monthly_additional_revenue * analysis_period_months
            
            # Create clear calculation explanations
            explanations = [
                f"Step 1: Monthly time saved from AI efficiency = {total_time_saved_hours:,.1f} hours",
                f"Step 2: Time allocated to new revenue projects = {time_allocated_to_new_projects:,.1f} hours ({total_time_saved_hours:,.1f} hours × {percent_time_to_new_projects:.1%} allocation)",
                f"Step 3: Additional monthly revenue = ${monthly_additional_revenue:,.2f} ({time_allocated_to_new_projects:,.1f} hours × ${revenue_per_employee_per_hour}/hour)",
                f"Step 4: Total revenue growth over {analysis_period_months} months = ${total_revenue_growth_period:,.2f}"
            ]
            
            results['revenue_growth'] = {
                'total_time_saved_hours_per_month': total_time_saved_hours,
                'time_allocated_to_new_projects_hours': time_allocated_to_new_projects,
                'percent_time_to_new_projects': percent_time_to_new_projects * 100,
                'revenue_per_employee_per_hour': revenue_per_employee_per_hour,
                'monthly_additional_revenue': monthly_additional_revenue,
                'total_revenue_growth_period': total_revenue_growth_period,
                'calculation_explanations': explanations
            }
        except Exception as e:
            error_msg = f'Error calculating revenue growth: {str(e)}'
            logger.exception(error_msg)
            return {'error': error_msg}
    
    # ========================================
    # STEP 4: Customer Churn Reduction Calculation
    # Calculates value from improved customer retention due to better service
    # ========================================
    if 'customer_churn_reduction' in params:
        try:
            churn_params = params['customer_churn_reduction']
            
            # Extract customer parameters
            total_customer_count = churn_params.get('total_customer_count')
            customer_churn_before_ai = churn_params.get('customer_churn_before_ai', 1.0) / 100
            customer_churn_after_ai = churn_params.get('customer_churn_after_ai', 0.5) / 100
            average_monthly_revenue_per_customer = churn_params.get('average_monthly_revenue_per_customer', 100)
            
            # Validate required parameters
            if total_customer_count is None:
                error_msg = 'Customer churn reduction component missing required parameter: total_customer_count'
                logger.error(error_msg)
                return {'error': error_msg}
            
            # Calculate the improvement in customer retention
            churn_reduction_rate = customer_churn_before_ai - customer_churn_after_ai
            customers_saved_per_month = total_customer_count * churn_reduction_rate
            
            # Value Component 1: Revenue retention from customers who don't churn
            monthly_revenue_retained = customers_saved_per_month * average_monthly_revenue_per_customer
            total_revenue_retained_period = monthly_revenue_retained * analysis_period_months
            
            # Value Component 2: Cost avoidance from not having to acquire replacement customers
            annual_revenue_per_customer = average_monthly_revenue_per_customer * 12
            cost_of_acquiring_new_customer = annual_revenue_per_customer * 0.20  # Industry standard: 20% of annual revenue
            monthly_acquisition_cost_avoided = customers_saved_per_month * cost_of_acquiring_new_customer
            total_acquisition_cost_avoided_period = monthly_acquisition_cost_avoided * analysis_period_months
            
            # Total value = revenue retention + cost avoidance
            monthly_total_churn_value = monthly_revenue_retained + monthly_acquisition_cost_avoided
            total_churn_reduction_value_period = total_revenue_retained_period + total_acquisition_cost_avoided_period
            
            # Create detailed calculation explanations
            explanations = [
                f"Step 1: Churn improvement = {churn_reduction_rate:.2%} ({customer_churn_before_ai:.2%} before AI - {customer_churn_after_ai:.2%} after AI)",
                f"Step 2: Customers saved monthly = {customers_saved_per_month:.1f} ({total_customer_count:,} customers × {churn_reduction_rate:.2%} improvement)",
                f"Step 3: Monthly revenue retained = ${monthly_revenue_retained:,.2f} ({customers_saved_per_month:.1f} customers × ${average_monthly_revenue_per_customer:,.2f}/month)",
                f"Step 4: Customer acquisition cost = ${cost_of_acquiring_new_customer:,.2f} (20% of ${annual_revenue_per_customer:,.2f} annual revenue)",
                f"Step 5: Monthly acquisition costs avoided = ${monthly_acquisition_cost_avoided:,.2f} ({customers_saved_per_month:.1f} customers × ${cost_of_acquiring_new_customer:,.2f})",
                f"Step 6: Total monthly churn value = ${monthly_total_churn_value:,.2f} (${monthly_revenue_retained:,.2f} retained + ${monthly_acquisition_cost_avoided:,.2f} costs avoided)",
                f"Step 7: Total value over {analysis_period_months} months = ${total_churn_reduction_value_period:,.2f}"
            ]
            
            results['customer_churn_reduction'] = {
                'total_customer_count': total_customer_count,
                'customer_churn_before_ai': customer_churn_before_ai * 100,
                'customer_churn_after_ai': customer_churn_after_ai * 100,
                'churn_reduction_rate': churn_reduction_rate * 100,
                'customers_saved_per_month': customers_saved_per_month,
                'average_monthly_revenue_per_customer': average_monthly_revenue_per_customer,
                'monthly_revenue_retained': monthly_revenue_retained,
                'cost_of_acquiring_new_customer': cost_of_acquiring_new_customer,
                'monthly_acquisition_cost_avoided': monthly_acquisition_cost_avoided,
                'monthly_total_churn_value': monthly_total_churn_value,
                'total_revenue_retained_period': total_revenue_retained_period,
                'total_acquisition_cost_avoided_period': total_acquisition_cost_avoided_period,
                'total_churn_reduction_value_period': total_churn_reduction_value_period,
                'calculation_explanations': explanations
            }
        except Exception as e:
            error_msg = f'Error calculating customer churn reduction: {str(e)}'
            logger.exception(error_msg)
            return {'error': error_msg}
    
    # Risk mitigation calculation - COMMENTED OUT FOR NOW
    # if 'risk_mitigation' in params:
    #     try:
    #         risk_params = params['risk_mitigation']
    #         
    #         # Extract parameters
    #         compliance_cost_avoidance = risk_params.get('compliance_cost_avoidance', 0)
    #         security_incident_cost_avoidance = risk_params.get('security_incident_cost_avoidance', 0)
    #         downtime_cost_avoidance = risk_params.get('downtime_cost_avoidance', 0)
    #         reputation_risk_value = risk_params.get('reputation_risk_value', 0)
    #         percent_risk_confidence = risk_params.get('percent_risk_confidence', 60) / 100
    #         
    #         # Calculate risk mitigation value
    #         monthly_risk_mitigation = compliance_cost_avoidance + security_incident_cost_avoidance + downtime_cost_avoidance + reputation_risk_value
    #         total_risk_mitigation_period = monthly_risk_mitigation * analysis_period_months
    #         confidence_adjusted_risk_mitigation = total_risk_mitigation_period * percent_risk_confidence
    #         
    #         # Create calculation explanations
    #         explanations = [
    #             f"1/ monthly_risk_mitigation (${monthly_risk_mitigation:,.2f}) = compliance_cost_avoidance (${compliance_cost_avoidance:,.2f}) + security_incident_cost_avoidance (${security_incident_cost_avoidance:,.2f}) + downtime_cost_avoidance (${downtime_cost_avoidance:,.2f}) + reputation_risk_value (${reputation_risk_value:,.2f})",
    #             f"2/ total_risk_mitigation_period (${total_risk_mitigation_period:,.2f}) = monthly_risk_mitigation (${monthly_risk_mitigation:,.2f}) * analysis_period_months ({analysis_period_months})",
    #             f"3/ confidence_adjusted_risk_mitigation (${confidence_adjusted_risk_mitigation:,.2f}) = total_risk_mitigation_period (${total_risk_mitigation_period:,.2f}) * percent_risk_confidence ({percent_risk_confidence:.1%})"
    #         ]
    #         
    #         results['risk_mitigation'] = {
    #             'monthly_compliance_avoidance': compliance_cost_avoidance,
    #             'monthly_security_avoidance': security_incident_cost_avoidance,
    #             'monthly_downtime_avoidance': downtime_cost_avoidance,
    #             'monthly_reputation_value': reputation_risk_value,
    #             'monthly_total_risk_mitigation': monthly_risk_mitigation,
    #             'total_risk_mitigation_period': total_risk_mitigation_period,
    #             'confidence_adjusted_risk_mitigation': confidence_adjusted_risk_mitigation,
    #             'confidence_level': percent_risk_confidence * 100,
    #             'calculation_explanations': explanations
    #         }
    #     except Exception as e:
    #         return {'error': f'Error calculating risk mitigation: {str(e)}'}
    
    # ========================================
    # STEP 5: Implementation Costs Calculation
    # Calculates one-time costs for implementing the AI Agent solution
    # ========================================
    if 'implementation_costs' in params:
        try:
            impl_params = params['implementation_costs']
            
            # Extract one-time cost parameters with defaults
            one_time_implementation_cost = impl_params.get('one_time_implementation_cost', 100000)
            one_time_training_cost = impl_params.get('one_time_training_cost', 20000)
            
            # Calculate total one-time implementation costs
            total_implementation_costs = one_time_implementation_cost + one_time_training_cost
            
            # Create clear calculation explanations
            explanations = [
                f"Step 1: Implementation cost = ${one_time_implementation_cost:,.2f} (setup, configuration, integration)",
                f"Step 2: Training cost = ${one_time_training_cost:,.2f} (employee training and change management)",
                f"Step 3: Total implementation costs = ${total_implementation_costs:,.2f} (one-time investment)"
            ]
            
            results['implementation_costs'] = {
                'one_time_implementation_cost': one_time_implementation_cost,
                'one_time_training_cost': one_time_training_cost,
                'total_implementation_costs': total_implementation_costs,
                'calculation_explanations': explanations
            }
        except Exception as e:
            error_msg = f'Error calculating implementation costs: {str(e)}'
            logger.exception(error_msg)
            return {'error': error_msg}
    
    # ========================================
    # STEP 6: Business Value Summary
    # Combines all benefits and costs to calculate overall ROI metrics
    # ========================================
    try:
        # Sum all calculated benefits
        total_benefits = 0
        total_benefits += results.get('cost_savings', {}).get('total_net_savings_period', 0)
        total_benefits += results.get('revenue_growth', {}).get('total_revenue_growth_period', 0)
        total_benefits += results.get('customer_churn_reduction', {}).get('total_churn_reduction_value_period', 0)
        # total_benefits += results.get('risk_mitigation', {}).get('confidence_adjusted_risk_mitigation', 0)  # COMMENTED OUT
        
        # Get implementation costs (one-time costs)
        total_costs = results.get('implementation_costs', {}).get('total_implementation_costs', 0)
        
        # Calculate net value and ROI
        net_value = total_benefits - total_costs
        # ROI calculation: (Net Value / Total Costs) * 100
        roi_percent = (net_value / total_costs * 100) if total_costs > 0 else float('inf') if total_benefits > 0 else 0
        
        # Calculate monthly net benefit for payback analysis
        monthly_net_benefit = 0
        if 'cost_savings' in results:
            monthly_net_benefit += results['cost_savings'].get('monthly_net_savings', 0)
        if 'revenue_growth' in results:
            monthly_net_benefit += results['revenue_growth'].get('monthly_additional_revenue', 0)
        if 'customer_churn_reduction' in results:
            monthly_net_benefit += results['customer_churn_reduction'].get('monthly_total_churn_value', 0)
        # if 'risk_mitigation' in results:  # COMMENTED OUT
        #     monthly_net_benefit += results['risk_mitigation'].get('monthly_total_risk_mitigation', 0)
        # if 'implementation_costs' in results:  # COMMENTED OUT FOR NOW
        #     monthly_net_benefit -= results['implementation_costs'].get('total_monthly_costs', 0)
        
        # Payback calculation based on initial investment
        initial_investment = results.get('implementation_costs', {}).get('total_implementation_costs', 0)
        
        # Payback period: time to recover initial investment through monthly benefits
        payback_months = (initial_investment / monthly_net_benefit) if monthly_net_benefit > 0 else float('inf')
        
        # Create clear summary explanations
        roi_display = "Infinite (pure benefit)" if roi_percent == float('inf') else f"{roi_percent:.1f}%"
        payback_display = "Never (costs exceed benefits)" if payback_months == float('inf') else f"{payback_months:.1f} months"
        
        summary_explanations = [
            f"Total Benefits: ${total_benefits:,.2f} (sum of all calculated value components over {analysis_period_months} months)",
            f"Total Costs: ${total_costs:,.2f} (one-time implementation and training costs)",
            f"Net Value: ${net_value:,.2f} (total benefits minus total costs)",
            f"ROI: {roi_display} (return on investment percentage)",
            f"Payback Period: {payback_display} (time to recover initial investment)",
            f"Monthly Net Benefit: ${monthly_net_benefit:,.2f} (ongoing monthly value creation)"
        ]
        
        results['business_value_summary'] = {
            'total_benefits': total_benefits,
            'total_costs': total_costs,
            'net_value': net_value,
            'roi_percent': roi_percent,
            'payback_months': payback_months,
            'monthly_net_benefit': monthly_net_benefit,
            'initial_investment': initial_investment,
            'analysis_period_months': analysis_period_months,
            'currency': currency,
            'calculation_explanations': summary_explanations
        }
        
    except Exception as e:
        error_msg = f'Error calculating business value summary: {str(e)}'
        logger.exception(error_msg)
        return {'error': error_msg}
    
    return results

@tool
def bva_what_if_analysis(
    base_params: dict,
    primary_variable: str,
    primary_range: List[Any],
    secondary_variable: Optional[str] = None,
    secondary_range: Optional[List[Any]] = None
) -> dict:
    """
    Performs what-if analysis on Business Value Analysis (BVA) metrics by varying 1-2 parameters while keeping others constant.
    Perfect for sensitivity analysis and heatmap visualization of ROI scenarios.
    
    Args:
        base_params: Base configuration dict (same format as bva_calculator)
        primary_variable: Parameter name to vary (e.g., "questions_per_month", "cost_savings.labor_cost_per_hour", "customer_churn_reduction.total_customer_count")
        primary_range: List of values for primary variable (e.g., [10000, 50000, 100000] or [50, 100, 150])
        secondary_variable: Optional second parameter to vary for 2D analysis
        secondary_range: List of values for secondary variable (any type)
        
    Returns:
        dict with:
        - analysis_type: "1D" or "2D"
        - primary_variable: Name and range of primary variable
        - secondary_variable: Name and range of secondary variable (if 2D)
        - results: BVA results for each scenario
        - roi_flat: Flattened ROI array for heatmap visualization
        - net_value_flat: Flattened net value array for heatmap visualization
        - payback_flat: Flattened payback period array for heatmap visualization
        - scenarios: List of scenario descriptions
    """
    
    # Initialize result containers
    results = []
    roi_flat = []
    net_value_flat = []
    payback_flat = []
    scenarios = []
    
    # Determine analysis type based on secondary variable presence
    is_2d = secondary_variable is not None and secondary_range is not None
    analysis_type = "2D" if is_2d else "1D"
    
    def set_nested_param(params_dict, param_path, value):
        """
        Set parameter that might be nested in the configuration.
        Examples: 
        - 'questions_per_month' -> params_dict['questions_per_month'] = value
        - 'cost_savings.labor_cost_per_hour' -> params_dict['cost_savings']['labor_cost_per_hour'] = value
        """
        if '.' in param_path:
            # Handle nested parameters (e.g., "cost_savings.labor_cost_per_hour")
            keys = param_path.split('.')
            current = params_dict
            # Navigate to the parent container
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            # Set the final value
            current[keys[-1]] = value
        else:
            # Handle top-level parameters (e.g., "questions_per_month")
            params_dict[param_path] = value
    
    try:
        if is_2d:
            # 2D Analysis: Create metrics matrix by varying both parameters
            for secondary_val in secondary_range:
                for primary_val in primary_range:
                    # Create deep copy of base configuration for this scenario
                    scenario_params = base_params.copy()
                    
                    # Apply parameter variations
                    set_nested_param(scenario_params, primary_variable, primary_val)
                    set_nested_param(scenario_params, secondary_variable, secondary_val)
                    
                    # Calculate BVA metrics for this parameter combination
                    result = bva_calculator(scenario_params)
                    
                    # Check for calculation errors
                    if 'error' in result:
                        error_msg = f'Calculation failed for {primary_variable}={primary_val}, {secondary_variable}={secondary_val}: {result["error"]}'
                        logger.error(error_msg)
                        return {'error': error_msg}
                    
                    # Extract key business metrics
                    business_summary = result.get('business_value_summary', {})
                    roi_percent = business_summary.get('roi_percent', 0)
                    net_value = business_summary.get('net_value', 0)
                    payback_months = business_summary.get('payback_months', float('inf'))
                    
                    # Handle infinite values for visualization
                    roi_display = roi_percent if roi_percent != float('inf') else 999999
                    payback_display = payback_months if payback_months != float('inf') else 999999
                    
                    # Store flattened arrays for heatmap visualization
                    roi_flat.append(roi_display)
                    net_value_flat.append(net_value)
                    payback_flat.append(payback_display)
                    
                    scenario_desc = f"{primary_variable}={primary_val}, {secondary_variable}={secondary_val}"
                    scenarios.append(scenario_desc)
                    
                    results.append({
                        'scenario': scenario_desc,
                        'primary_value': primary_val,
                        'secondary_value': secondary_val,
                        'roi_percent': roi_percent,
                        'net_value': net_value,
                        'payback_months': payback_months,
                        'detailed_results': result
                    })
        else:
            # 1D Analysis: Vary only the primary parameter
            for primary_val in primary_range:
                # Create deep copy of base configuration for this scenario
                scenario_params = base_params.copy()
                
                # Apply parameter variation
                set_nested_param(scenario_params, primary_variable, primary_val)
                
                # Calculate BVA metrics for this parameter value
                result = bva_calculator(scenario_params)
                
                # Check for calculation errors
                if 'error' in result:
                    error_msg = f'Calculation failed for {primary_variable}={primary_val}: {result["error"]}'
                    logger.error(error_msg)
                    return {'error': error_msg}
                
                # Extract key business metrics
                business_summary = result.get('business_value_summary', {})
                roi_percent = business_summary.get('roi_percent', 0)
                net_value = business_summary.get('net_value', 0)
                payback_months = business_summary.get('payback_months', float('inf'))
                
                # Handle infinite values for visualization
                roi_display = roi_percent if roi_percent != float('inf') else 999999
                payback_display = payback_months if payback_months != float('inf') else 999999
                
                # Store flattened arrays for visualization
                roi_flat.append(roi_display)
                net_value_flat.append(net_value)
                payback_flat.append(payback_display)
                
                scenario_desc = f"{primary_variable}={primary_val}"
                scenarios.append(scenario_desc)
                
                results.append({
                    'scenario': scenario_desc,
                    'primary_value': primary_val,
                    'roi_percent': roi_percent,
                    'net_value': net_value,
                    'payback_months': payback_months,
                    'detailed_results': result
                })
        
        # Calculate sensitivity metrics for business insights
        finite_roi = [x for x in roi_flat if x != 999999]
        finite_payback = [x for x in payback_flat if x != 999999]
        
        # Compile final analysis results
        return {
            'analysis_type': analysis_type,
            'primary_variable': {
                'name': primary_variable,
                'range': primary_range
            },
            'secondary_variable': {
                'name': secondary_variable,
                'range': secondary_range
            } if is_2d else None,
            'results': results,                           # Detailed results for each scenario
            'roi_flat': roi_flat,                        # Flattened ROI array for heatmap
            'net_value_flat': net_value_flat,            # Flattened net value array for heatmap
            'payback_flat': payback_flat,                # Flattened payback period array for heatmap
            'scenarios': scenarios,                      # Scenario descriptions for labels
            'sensitivity_metrics': {
                'min_roi': min(finite_roi) if finite_roi else 0,
                'max_roi': max(finite_roi) if finite_roi else 0,
                'roi_range': max(finite_roi) - min(finite_roi) if finite_roi else 0,
                'min_net_value': min(net_value_flat),
                'max_net_value': max(net_value_flat),
                'net_value_range': max(net_value_flat) - min(net_value_flat),
                'min_payback': min(finite_payback) if finite_payback else 0,
                'max_payback': max(finite_payback) if finite_payback else 0,
                'payback_range': max(finite_payback) - min(finite_payback) if finite_payback else 0
            }
        }
        
    except Exception as e:
        error_msg = f'What-if analysis failed: {str(e)}'
        logger.exception(error_msg)
        return {'error': error_msg}