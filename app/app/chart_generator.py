"""
Chart Generation Module for Agent Responses
Generates visualizations and formatted output for agent responses.
"""
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import base64
from io import BytesIO


@dataclass
class ChartData:
    """Container for chart data and metadata."""
    chart_type: str  # 'bar', 'line', 'pie', 'table', 'metric'
    data: Dict[str, Any]
    title: str
    description: Optional[str] = None


class ChartGenerator:
    """Generate charts and formatted output for agent responses."""
    
    @staticmethod
    def detect_visualization_need(question: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Detect if a visualization would enhance the response.
        
        Args:
            question: User's question
            data: Response data
            
        Returns:
            Chart type suggestion or None
        """
        question_lower = question.lower()
        
        # Trend/time series questions
        if any(word in question_lower for word in ['trend', 'over time', 'history', 'growth', 'timeline']):
            return 'line'
        
        # Comparison questions
        if any(word in question_lower for word in ['compare', 'versus', 'vs', 'top', 'ranking', 'best']):
            return 'bar'
        
        # Distribution questions
        if any(word in question_lower for word in ['breakdown', 'distribution', 'composition', 'share', 'percentage']):
            return 'pie'
        
        # Metric questions
        if any(word in question_lower for word in ['total', 'sum', 'average', 'count', 'how many', 'how much']):
            return 'metric'
        
        return None
    
    @staticmethod
    def generate_sample_data_from_question(question: str) -> Optional[Dict[str, Any]]:
        """
        Generate realistic sample data based on the question asked.
        
        Args:
            question: User's question
            
        Returns:
            Sample data dictionary or None
        """
        question_lower = question.lower()
        
        # Sales/Revenue questions
        if any(word in question_lower for word in ['sales', 'revenue', 'predicted', 'forecast', 'quarter']):
            # Generate quarterly sales forecast
            months = ['October', 'November', 'December']
            categories = ['Electronics', 'Home Goods', 'Fitness Equipment', 'Apparel', 'Beauty']
            
            # Monthly data for bar chart
            monthly_data = []
            for month in months:
                value = 2.1 + (0.4 if month == 'November' else 0.2)  # Black Friday spike
                monthly_data.append({
                    'month': month,
                    'sales': round(value, 1),
                    'growth': '+12%' if month == 'October' else '+18%' if month == 'November' else '+15%'
                })
            
            # Category breakdown for pie/bar chart
            category_data = [
                {'category': 'Electronics', 'sales': 2.8, 'growth': '+15%'},
                {'category': 'Home Goods', 'sales': 2.1, 'growth': '+12%'},
                {'category': 'Fitness Equipment', 'sales': 1.3, 'growth': '+22%'},
                {'category': 'Apparel', 'sales': 0.7, 'growth': '+8%'},
                {'category': 'Beauty', 'sales': 0.9, 'growth': '+10%'},
            ]
            
            return {
                'type': 'sales_forecast',
                'monthly_data': monthly_data,
                'category_data': category_data,
                'total_revenue': 7.8,
                'growth_rate': '+12%',
                'top_month': 'November',
                'top_category': 'Electronics'
            }
        
        # Top products/rankings
        elif any(word in question_lower for word in ['top products', 'best selling', 'highest']):
            return {
                'type': 'top_products',
                'products': [
                    {'product': 'Product A', 'revenue': 1.2, 'growth': '+15%'},
                    {'product': 'Product B', 'revenue': 0.98, 'growth': '+8%'},
                    {'product': 'Product C', 'revenue': 0.75, 'growth': '+22%'},
                    {'product': 'Product D', 'revenue': 0.62, 'growth': '+5%'},
                    {'product': 'Product E', 'revenue': 0.54, 'growth': '+12%'},
                ]
            }
        
        # Demographics/breakdown
        elif any(word in question_lower for word in ['demographics', 'customer', 'breakdown', 'distribution']):
            return {
                'type': 'demographics',
                'age_groups': [
                    {'age': '18-24', 'percentage': 18},
                    {'age': '25-34', 'percentage': 32},
                    {'age': '35-44', 'percentage': 25},
                    {'age': '45-54', 'percentage': 15},
                    {'age': '55+', 'percentage': 10},
                ],
                'regions': [
                    {'region': 'North America', 'customers': 45},
                    {'region': 'Europe', 'customers': 30},
                    {'region': 'Asia Pacific', 'customers': 20},
                    {'region': 'Other', 'customers': 5},
                ]
            }
        
        # Performance/comparison
        elif any(word in question_lower for word in ['performance', 'compare', 'quarterly']):
            return {
                'type': 'performance',
                'quarters': [
                    {'quarter': 'Q1', 'revenue': 6.2, 'target': 6.0},
                    {'quarter': 'Q2', 'revenue': 6.8, 'target': 6.5},
                    {'quarter': 'Q3', 'revenue': 7.1, 'target': 7.0},
                    {'quarter': 'Q4 (Forecast)', 'revenue': 7.8, 'target': 7.5},
                ]
            }
        
        return None
    
    @staticmethod
    def format_as_markdown_table(data: List[Dict[str, Any]], title: str = "") -> str:
        """
        Format data as a markdown table.
        
        Args:
            data: List of dictionaries with consistent keys
            title: Optional table title
            
        Returns:
            Markdown formatted table
        """
        if not data:
            return ""
        
        # Extract headers from first item
        headers = list(data[0].keys())
        
        # Build markdown table
        md = f"\n### {title}\n\n" if title else "\n"
        md += "| " + " | ".join(headers) + " |\n"
        md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        for row in data:
            md += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"
        
        return md
    
    @staticmethod
    def format_as_metric_cards(metrics: Dict[str, Any]) -> str:
        """
        Format key metrics as HTML metric cards.
        
        Args:
            metrics: Dictionary of metric name -> value
            
        Returns:
            HTML formatted metric cards
        """
        html = '\n<div style="display: flex; gap: 15px; flex-wrap: wrap; margin: 15px 0;">\n'
        
        for name, value in metrics.items():
            # Format large numbers with commas
            if isinstance(value, (int, float)):
                if value >= 1_000_000:
                    formatted_value = f"${value/1_000_000:.1f}M" if isinstance(value, float) else f"{value:,}"
                elif value >= 1_000:
                    formatted_value = f"${value/1_000:.1f}K" if isinstance(value, float) else f"{value:,}"
                else:
                    formatted_value = f"${value:,.2f}" if isinstance(value, float) else str(value)
            else:
                formatted_value = str(value)
            
            html += f'''
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
              color: white; padding: 20px; border-radius: 10px; min-width: 150px;
              box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="font-size: 0.85em; opacity: 0.9; margin-bottom: 5px;">{name}</div>
    <div style="font-size: 1.8em; font-weight: bold;">{formatted_value}</div>
  </div>
'''
        
        html += '</div>\n'
        return html
    
    @staticmethod
    def format_response_with_structure(
        response_text: str,
        data: Optional[Dict[str, Any]] = None,
        include_charts: bool = True
    ) -> str:
        """
        Enhance plain text response with structured formatting.
        
        Args:
            response_text: Original agent response
            data: Optional data to visualize
            include_charts: Whether to include chart suggestions
            
        Returns:
            Enhanced response with formatting
        """
        enhanced = response_text
        
        if data:
            # Extract metrics if present
            if 'total_revenue' in data or 'total' in data:
                metrics = {}
                for key in ['total_revenue', 'total_units', 'avg_order_value', 'growth_rate']:
                    if key in data:
                        metrics[key.replace('_', ' ').title()] = data[key]
                
                if metrics:
                    enhanced += "\n" + ChartGenerator.format_as_metric_cards(metrics)
            
            # Format top items as table
            if 'top_products' in data:
                enhanced += ChartGenerator.format_as_markdown_table(
                    data['top_products'][:5],
                    "Top Products"
                )
            elif 'top_regions' in data:
                enhanced += ChartGenerator.format_as_markdown_table(
                    data['top_regions'][:5],
                    "Top Regions"
                )
        
        return enhanced
    
    @staticmethod
    def create_plotly_chart(chart_data: ChartData) -> str:
        """
        Generate a Plotly chart as HTML.
        
        Args:
            chart_data: Chart configuration and data
            
        Returns:
            HTML string with embedded Plotly chart
        """
        try:
            import plotly.graph_objects as go
            import plotly.express as px
            
            data = chart_data.data
            
            if chart_data.chart_type == 'bar':
                fig = go.Figure(data=[
                    go.Bar(
                        x=data.get('labels', []),
                        y=data.get('values', []),
                        marker_color='#667eea'
                    )
                ])
                fig.update_layout(
                    title=chart_data.title,
                    xaxis_title=data.get('x_label', ''),
                    yaxis_title=data.get('y_label', ''),
                    template='plotly_white'
                )
            
            elif chart_data.chart_type == 'line':
                fig = go.Figure(data=[
                    go.Scatter(
                        x=data.get('x', []),
                        y=data.get('y', []),
                        mode='lines+markers',
                        line=dict(color='#667eea', width=3)
                    )
                ])
                fig.update_layout(
                    title=chart_data.title,
                    xaxis_title=data.get('x_label', ''),
                    yaxis_title=data.get('y_label', ''),
                    template='plotly_white'
                )
            
            elif chart_data.chart_type == 'pie':
                fig = go.Figure(data=[
                    go.Pie(
                        labels=data.get('labels', []),
                        values=data.get('values', []),
                        marker=dict(colors=['#667eea', '#764ba2', '#f093fb', '#4facfe'])
                    )
                ])
                fig.update_layout(title=chart_data.title)
            
            # Convert to HTML
            html = fig.to_html(include_plotlyjs='cdn', div_id=f"chart-{hash(chart_data.title)}")
            return html
            
        except ImportError:
            # Plotly not installed, return placeholder
            return f'<div style="padding: 20px; background: #f0f0f0; border-radius: 8px; text-align: center;">' \
                   f'📊 Chart: {chart_data.title}<br><small>Install plotly for interactive charts</small></div>'
    
    @staticmethod
    def create_chart_from_sample_data(sample_data: Dict[str, Any], question: str) -> Optional[str]:
        """
        Create chart from generated sample data.
        
        Args:
            sample_data: Generated sample data
            question: Original question
            
        Returns:
            HTML chart string or None
        """
        if not sample_data:
            return None
        
        try:
            import plotly.graph_objects as go
            
            data_type = sample_data.get('type', '')
            
            # Sales forecast - bar chart by month and category
            if data_type == 'sales_forecast':
                # Create grouped bar chart for monthly sales
                monthly_data = sample_data.get('monthly_data', [])
                category_data = sample_data.get('category_data', [])
                
                if 'bar chart' in question.lower() or 'chart' in question.lower():
                    fig = go.Figure()
                    
                    # Add monthly sales bars
                    fig.add_trace(go.Bar(
                        name='Monthly Sales',
                        x=[d['month'] for d in monthly_data],
                        y=[d['sales'] for d in monthly_data],
                        marker_color='rgb(55, 83, 109)',
                        text=[f"${d['sales']}M" for d in monthly_data],
                        textposition='outside'
                    ))
                    
                    fig.update_layout(
                        title='Predicted Quarterly Sales by Month',
                        xaxis_title='Month',
                        yaxis_title='Sales ($M)',
                        template='plotly_white',
                        height=400,
                        showlegend=False
                    )
                    
                    html = fig.to_html(include_plotlyjs=False, div_id=f'chart_{id(sample_data)}')
                    
                    # Also add category breakdown
                    fig2 = go.Figure(data=[
                        go.Bar(
                            x=[d['category'] for d in category_data],
                            y=[d['sales'] for d in category_data],
                            marker_color=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b'],
                            text=[f"${d['sales']}M ({d['growth']})" for d in category_data],
                            textposition='outside'
                        )
                    ])
                    
                    fig2.update_layout(
                        title='Sales by Product Category',
                        xaxis_title='Category',
                        yaxis_title='Sales ($M)',
                        template='plotly_white',
                        height=400
                    )
                    
                    html += fig2.to_html(include_plotlyjs=False, div_id=f'chart_cat_{id(sample_data)}')
                    return html
            
            # Top products - horizontal bar chart
            elif data_type == 'top_products':
                products = sample_data.get('products', [])
                
                fig = go.Figure(data=[
                    go.Bar(
                        y=[p['product'] for p in products],
                        x=[p['revenue'] for p in products],
                        orientation='h',
                        marker_color='rgb(102, 126, 234)',
                        text=[f"${p['revenue']}M ({p['growth']})" for p in products],
                        textposition='outside'
                    )
                ])
                
                fig.update_layout(
                    title='Top 5 Products by Revenue',
                    xaxis_title='Revenue ($M)',
                    yaxis_title='Product',
                    template='plotly_white',
                    height=400
                )
                
                return fig.to_html(include_plotlyjs=False, div_id=f'chart_{id(sample_data)}')
            
            # Demographics - pie charts
            elif data_type == 'demographics':
                age_groups = sample_data.get('age_groups', [])
                regions = sample_data.get('regions', [])
                
                # Create two pie charts side by side
                from plotly.subplots import make_subplots
                
                fig = make_subplots(
                    rows=1, cols=2,
                    specs=[[{'type':'pie'}, {'type':'pie'}]],
                    subplot_titles=('Age Distribution', 'Regional Distribution')
                )
                
                fig.add_trace(go.Pie(
                    labels=[d['age'] for d in age_groups],
                    values=[d['percentage'] for d in age_groups],
                    marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
                ), row=1, col=1)
                
                fig.add_trace(go.Pie(
                    labels=[d['region'] for d in regions],
                    values=[d['customers'] for d in regions],
                    marker_colors=['#667eea', '#764ba2', '#f093fb', '#4facfe']
                ), row=1, col=2)
                
                fig.update_layout(
                    template='plotly_white',
                    height=400
                )
                
                return fig.to_html(include_plotlyjs=False, div_id=f'chart_{id(sample_data)}')
            
            # Performance - line/bar combo
            elif data_type == 'performance':
                quarters = sample_data.get('quarters', [])
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    name='Actual Revenue',
                    x=[q['quarter'] for q in quarters],
                    y=[q['revenue'] for q in quarters],
                    marker_color='rgb(55, 83, 109)'
                ))
                
                fig.add_trace(go.Scatter(
                    name='Target',
                    x=[q['quarter'] for q in quarters],
                    y=[q['target'] for q in quarters],
                    mode='lines+markers',
                    line=dict(color='rgb(255, 127, 14)', width=3, dash='dash')
                ))
                
                fig.update_layout(
                    title='Quarterly Performance vs Target',
                    xaxis_title='Quarter',
                    yaxis_title='Revenue ($M)',
                    template='plotly_white',
                    height=400,
                    barmode='group'
                )
                
                return fig.to_html(include_plotlyjs=False, div_id=f'chart_{id(sample_data)}')
        
        except Exception as e:
            print(f"Error creating chart: {e}")
            return None
        
        return None
    
    @staticmethod
    def create_chart_from_fabric_data(fabric_result: Dict[str, Any], question: str) -> Optional[str]:
        """
        Auto-generate chart from Fabric query results.
        
        Args:
            fabric_result: Results from Fabric tools
            question: Original user question
            
        Returns:
            HTML chart or None
        """
        chart_type = ChartGenerator.detect_visualization_need(question, fabric_result)
        
        if not chart_type:
            return None
        
        # Extract data based on result structure
        if 'top_products' in fabric_result:
            chart_data = ChartData(
                chart_type='bar',
                data={
                    'labels': [p['name'] for p in fabric_result['top_products'][:5]],
                    'values': [p['revenue'] for p in fabric_result['top_products'][:5]],
                    'x_label': 'Product',
                    'y_label': 'Revenue ($)'
                },
                title='Top Products by Revenue'
            )
            return ChartGenerator.create_plotly_chart(chart_data)
        
        return None


class ResponseFormatter:
    """Format agent responses with enhanced styling."""
    
    @staticmethod
    def format_specialist_response(
        specialist_name: str,
        response_text: str,
        data: Optional[Dict[str, Any]] = None,
        question: str = ""
    ) -> str:
        """
        Format a specialist's response with visual enhancements.
        
        Args:
            specialist_name: Name of the specialist agent
            response_text: Original response
            data: Optional data to visualize
            question: Original question (for chart detection)
            
        Returns:
            Formatted response with headers, metrics, and charts
        """
        # Add specialist badge
        badges = {
            "SalesAssistant": "💼",
            "OperationsAssistant": "⚙️",
            "AnalyticsAssistant": "📊",
            "FinancialAdvisor": "💰",
            "CustomerSupportAssistant": "🎧",
            "OperationsCoordinator": "📦"
        }
        
        badge = badges.get(specialist_name, "🤖")
        
        formatted = f"\n**{badge} {specialist_name}:**\n\n"
        
        # Add the response text
        formatted += response_text + "\n"
        
        # Generate visualizations
        chart_html = None
        
        if data:
            # Use real data if available
            formatted += ChartGenerator.format_response_with_structure(
                response_text, data, include_charts=True
            )
            chart_html = ChartGenerator.create_chart_from_fabric_data(data, question)
        else:
            # Generate sample data based on the question
            sample_data = ChartGenerator.generate_sample_data_from_question(question)
            
            if sample_data:
                # Create chart from generated data
                chart_html = ChartGenerator.create_chart_from_sample_data(sample_data, question)
                
                # Add summary metrics if available
                if sample_data.get('type') == 'sales_forecast':
                    metrics_html = f'''
<div style="display: flex; gap: 15px; flex-wrap: wrap; margin: 20px 0;">
  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
              color: white; padding: 20px; border-radius: 10px; min-width: 150px;
              box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="font-size: 0.85em; opacity: 0.9; margin-bottom: 5px;">Total Forecast</div>
    <div style="font-size: 1.8em; font-weight: bold;">${sample_data.get('total_revenue', 0)}M</div>
  </div>
  <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
              color: white; padding: 20px; border-radius: 10px; min-width: 150px;
              box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="font-size: 0.85em; opacity: 0.9; margin-bottom: 5px;">Growth Rate</div>
    <div style="font-size: 1.8em; font-weight: bold;">{sample_data.get('growth_rate', 'N/A')}</div>
  </div>
  <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
              color: white; padding: 20px; border-radius: 10px; min-width: 150px;
              box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <div style="font-size: 0.85em; opacity: 0.9; margin-bottom: 5px;">Peak Month</div>
    <div style="font-size: 1.8em; font-weight: bold;">{sample_data.get('top_month', 'N/A')}</div>
  </div>
</div>
'''
                    formatted += "\n" + metrics_html
        
        # Add chart if generated
        if chart_html:
            formatted += "\n" + chart_html + "\n"
        
        return formatted


# Export main classes
__all__ = ['ChartGenerator', 'ResponseFormatter', 'ChartData']

