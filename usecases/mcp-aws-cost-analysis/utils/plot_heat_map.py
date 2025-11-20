from strands import tool
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from typing import List, Optional, Union
import json

def parse_values(values):
    """
    Parse values parameter that may be a list, nested list, or JSON string.
    
    Handles these cases:
    1. Direct list: [100, 200, 300] 
    2. Direct nested list: [[100, 200], [300, 400]]
    3. JSON string from tool interface: "[[100, 200], [300, 400]]"
    4. JSON string from tool interface: "[100, 200, 300]"
    
    Returns the parsed list structure.
    """
    if isinstance(values, str):
        try:
            # Tool interface converted list to string - parse it back
            return json.loads(values)
        except json.JSONDecodeError:
            # If JSON parsing fails, try eval as fallback (less safe but handles edge cases)
            try:
                return eval(values)
            except:
                raise ValueError(f"Cannot parse values parameter: {values}")
    else:
        # Already a proper list structure
        return values

def format_number(value):
    """Format numbers with K, M, B suffixes for better readability"""
    if abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:.1f}B"
    elif abs(value) >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:.0f}"

@tool
def plot_bar_chart(
    title: str,
    y_axis_title: str,
    x_axis_title: str,
    y_axis_items: List[str],
    x_axis_items: List[str],
    values: List[float],
    color_type: str,
    assumptions: List[str],
    current_x_value: Optional[str] = None,
    filename: Optional[str] = None
) -> dict:
    """
    Creates a bar chart for data visualization with intensity-based coloring.
    
    Args:
        title: Title of the chart
        y_axis_title: Y-axis label
        x_axis_title: X-axis label  
        y_axis_items: List of y-axis category names (not used for bar charts)
        x_axis_items: List of x-axis category names
        values: 1D list of numbers to plot (e.g., [10, 20, 30, 15]) - must be integers or floats
        color_type: Color scheme - "cost" (red), "time_savings" (blue), "revenue" (green), or any matplotlib colormap name (e.g., "Purples", "Oranges", "Greys")
        assumptions: List of most important and relevant assumptions to display on right side (e.g., ["30 days per month", "2 events per question"])
        current_x_value: Optional x-axis value to highlight as current use-case (e.g., "Medium Usage")
        filename: Optional filename to save chart as PNG (e.g., "my_chart.png")
        
    Returns:
        dict: Status and file path if saved
    """
    # Parse values parameter (handles both direct lists and JSON strings from tool interface)
    values = parse_values(values)
    
    # Set color based on type with intensity mapping
    color_maps = {
        "cost": plt.cm.Reds,
        "time_savings": plt.cm.Blues,
        "revenue": plt.cm.Greens
    }
    # Allow any matplotlib colormap name as fallback
    try:
        cmap = color_maps.get(color_type.lower()) or getattr(plt.cm, color_type)
    except AttributeError:
        cmap = plt.cm.Blues  # Default fallback
    
    # Normalize values for color intensity (light = small, dark = large)
    norm = plt.Normalize(vmin=min(values), vmax=max(values))
    colors = [cmap(norm(value)) for value in values]
    
    # Highlight current use-case with border
    edge_colors = ['red' if x == current_x_value else 'black' for x in x_axis_items]
    line_widths = [3 if x == current_x_value else 1 for x in x_axis_items]
    
    # Create figure with adaptive size and subplots for chart and assumptions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={'width_ratios': [3, 1]})
    
    # Create bar chart with professional styling
    bars = ax1.bar(x_axis_items, values, color=colors, edgecolor=edge_colors, linewidth=line_widths,
                   alpha=0.8)  # Slight transparency for professional look
    
    # Add grid for better readability
    ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
    ax1.set_axisbelow(True)  # Put grid behind bars
    
    # Add data labels on bars with better formatting
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                format_number(value), ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    # Set labels and title with professional styling
    ax1.set_title(title, fontsize=14, fontweight='bold', pad=20)
    ax1.set_xlabel(x_axis_title, fontsize=12, fontweight='bold')
    ax1.set_ylabel(y_axis_title, fontsize=12, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45, labelsize=10)
    ax1.tick_params(axis='y', labelsize=10)
    
    # Add current use-case legend if highlighted
    if current_x_value and current_x_value in x_axis_items:
        pass  # Keep highlighting but remove legend text
    
    # Display assumptions with professional formatting (matching heatmap style)
    ax2.axis('off')
    assumptions_text = "ASSUMPTIONS\n\n" + "\n".join([f"• {assumption}" for assumption in assumptions])
    
    ax2.text(0.05, 0.95, assumptions_text,
             transform=ax2.transAxes,
             fontsize=10,
             verticalalignment='top',
             fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    
    # Save if filename provided
    result = {"status": "success", "displayed": True}
    if filename:
        if not filename.endswith('.png'):
            filename += '.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        result["saved_to"] = filename
    
    # Always display
    plt.show()
    
    return result

@tool
def plot_heat_map(
    title: str,
    y_axis_title: str,
    x_axis_title: str,
    y_axis_items: List[str],
    x_axis_items: List[str],
    values_flat: List[float],  # Flattened values - no nested lists
    heatmap_type: str,
    color_type: str,
    assumptions: List[str],
    current_x_value: Optional[str] = None,
    current_y_value: Optional[str] = None,
    labels_flat: Optional[List[str]] = None,  # Flattened labels - no nested lists
    filename: Optional[str] = None
) -> dict:
    """
    Creates 1D or 2D heatmaps for sensitivity analysis with current use-case highlighting.
    
    Usage with Strands Agent:
    1D Example: 
    plot_heat_map(
        title="Cost by Usage Level",
        x_axis_title="Usage", y_axis_title="Cost ($)",
        x_axis_items=["Low", "Med", "High"], y_axis_items=[],
        values_flat=[100, 200, 300], heatmap_type="1D", color_type="cost",
        assumptions=["Monthly pricing"], current_x_value="Med",
        labels_flat=["$100", "$200", "$300"]
    )
    
    2D Example (3x2 grid):
    plot_heat_map(
        title="Cost by Team & Usage",
        x_axis_title="Usage", y_axis_title="Team Size", 
        x_axis_items=["Low", "High"], y_axis_items=["Small", "Med", "Large"],
        values_flat=[100, 200, 300, 400, 500, 600], heatmap_type="2D", color_type="cost",
        assumptions=["Monthly pricing"], current_x_value="Low", current_y_value="Small",
        labels_flat=["Basic", "Standard", "Pro", "Enterprise", "Premium", "Ultimate"]
    )
    Note: For 2D, values_flat is row-by-row: [row1_col1, row1_col2, row2_col1, row2_col2, ...]
    
    Args:
        title: Title of the chart
        y_axis_title: Y-axis label
        x_axis_title: X-axis label
        y_axis_items: List of y-axis category names
        x_axis_items: List of x-axis category names
        values_flat: Flattened list of numbers - for 2D, provide row-by-row [10, 20, 30, 40] means [[10,20],[30,40]]
        heatmap_type: "1D" for 1-dimensional heatmap, "2D" for 2-dimensional heatmap
        color_type: Color scheme - "cost" (red), "time_savings" (blue), "revenue" (green), or any matplotlib colormap name (e.g., "Purples", "Oranges", "Greys")
        assumptions: List of most important and relevant assumptions to display on right side (e.g., ["30 days per month", "2 events per question"])
        current_x_value: Optional x-axis value to highlight as current use-case (e.g., "Medium Usage")
        current_y_value: Optional y-axis value to highlight as current use-case (e.g., "50 Users") - only for 2D heatmaps
        labels_flat: Optional custom labels flattened same as values_flat (e.g., ["Low", "Med", "High", "Max"])
        filename: Optional filename to save chart as PNG (e.g., "my_heatmap.png")
        
    Returns:
        dict: Status and file path if saved
    """
    # Convert flattened values to proper structure based on heatmap type
    if heatmap_type == "1D":
        values = values_flat  # Use as-is for 1D
        labels = labels_flat  # Use as-is for 1D
    elif heatmap_type == "2D":
        # Reshape flattened values into 2D array: rows x cols
        num_rows = len(y_axis_items)
        num_cols = len(x_axis_items)
        if len(values_flat) != num_rows * num_cols:
            raise ValueError(f"values_flat length ({len(values_flat)}) must equal rows×cols ({num_rows}×{num_cols}={num_rows*num_cols})")
        
        # Convert flat list to 2D: [1,2,3,4] with 2 cols → [[1,2],[3,4]]
        values = [values_flat[i*num_cols:(i+1)*num_cols] for i in range(num_rows)]
        
        # Convert flat labels to 2D if provided
        if labels_flat:
            if len(labels_flat) != num_rows * num_cols:
                raise ValueError(f"labels_flat length ({len(labels_flat)}) must equal rows×cols ({num_rows}×{num_cols}={num_rows*num_cols})")
            labels = [labels_flat[i*num_cols:(i+1)*num_cols] for i in range(num_rows)]
        else:
            labels = None
    
    # Set colormap based on type
    cmap_map = {
        "cost": "Reds",
        "time_savings": "Blues", 
        "revenue": "Greens"
    }
    # Allow any matplotlib colormap name as fallback
    cmap = cmap_map.get(color_type.lower(), color_type if hasattr(plt.cm, color_type) else "Blues")
    
    # Calculate adaptive figure size based on data dimensions and assumptions
    if heatmap_type == "2D":
        width = max(8, len(x_axis_items) * 0.8)
        height = max(4, len(y_axis_items) * 0.6)
    else:
        width = max(8, len(x_axis_items) * 0.5)
        height = 4
    
    # Ensure height accommodates assumptions (roughly 0.5 inches per assumption)
    min_height_for_assumptions = max(3, len(assumptions) * 0.5 + 1)
    height = max(height, min_height_for_assumptions)
    
    # Create figure with adaptive size and subplots for chart and assumptions
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(width + 4, height), gridspec_kw={'width_ratios': [3, 1]})
    
    if heatmap_type == "1D":
        # Convert 1D values to 2D for heatmap (single row)
        data = np.array(values).reshape(1, -1)
        
        # Create heatmap with built-in annotations
        sns.heatmap(data, 
                   xticklabels=x_axis_items,
                   yticklabels=[y_axis_title] if y_axis_items else [''],
                   annot=True, fmt='.0f',
                   cmap=cmap,
                   cbar_kws={'label': y_axis_title},
                   linewidths=2, linecolor='white',
                   ax=ax1)
        
        # Format annotations with custom labels if provided
        if labels:
            for i, t in enumerate(ax1.texts):
                t.set_text(labels[i])
    
    elif heatmap_type == "2D":
        # Convert to numpy array
        data = np.array(values)
        
        # Create heatmap with built-in annotations
        sns.heatmap(data,
                   xticklabels=x_axis_items,
                   yticklabels=y_axis_items,
                   annot=True, fmt='.0f',
                   cmap=cmap,
                   cbar_kws={'label': 'Values'},
                   linewidths=2, linecolor='white',
                   ax=ax1)
        
        # Format annotations with custom labels if provided
        if labels:
            for i, t in enumerate(ax1.texts):
                row = i // len(x_axis_items)
                col = i % len(x_axis_items)
                t.set_text(labels[row][col])
    
    # Highlight current use-case cell with rectangle
    if current_x_value and current_x_value in x_axis_items:
        x_idx = x_axis_items.index(current_x_value)
        if heatmap_type == "1D":
            from matplotlib.patches import Rectangle
            rect = Rectangle((x_idx, 0), 1, 1, fill=False, edgecolor='blue', linewidth=4)
            ax1.add_patch(rect)
        elif heatmap_type == "2D" and current_y_value and current_y_value in y_axis_items:
            y_idx = y_axis_items.index(current_y_value)
            from matplotlib.patches import Rectangle
            rect = Rectangle((x_idx, y_idx), 1, 1, fill=False, edgecolor='blue', linewidth=4)
            ax1.add_patch(rect)
    
    # Set labels and title for heatmap
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.set_xlabel(x_axis_title, fontsize=12)
    ax1.set_ylabel(y_axis_title, fontsize=12)
    
    # Display assumptions with professional formatting
    ax2.axis('off')
    assumptions_text = "ASSUMPTIONS\n\n" + "\n".join([f"• {assumption}" for assumption in assumptions])
    
    ax2.text(0.05, 0.95, assumptions_text,
             transform=ax2.transAxes,
             fontsize=10,
             verticalalignment='top',
             fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    
    # Save if filename provided
    result = {"status": "success", "displayed": True, "type": heatmap_type}
    if filename:
        if not filename.endswith('.png'):
            filename += '.png'
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        result["saved_to"] = filename
    
    # Always display
    plt.show()
    
    return result
