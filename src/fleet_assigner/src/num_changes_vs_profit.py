import matplotlib.pyplot as plt

num_changes = [0, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000, 1050]
profit = [-9602989.76, -8924573.83, -8560692.04, -8315100.76, -8101993.64, -7886501.68, -7701899.81, -7546574.01, -7406696.04, -7278987.05, -7159245.49, -7051374.02, -6944072.42, -6845796.13, -6758784.92, -6673850.09, -6594563.12, -6519041.47, -6447699.74, -6382346.12, -6319841.159192413, -6262085.424490988]

plt.figure(figsize=(12, 6))
plt.plot(num_changes, profit, 'b-o', linewidth=2, markersize=6, markerfacecolor='red')
plt.xlabel('Number of Changes')
plt.ylabel('Profit ($)')
plt.title('Profit vs Number of Changes')
plt.grid(True, alpha=0.3)

# Format y-axis to show values in millions
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))

# Rotate x-axis labels for better readability
plt.xticks(rotation=45)

plt.tight_layout()

# Save the chart to a file
plt.savefig('profit_vs_changes.png', dpi=300, bbox_inches='tight')
plt.savefig('profit_vs_changes.pdf', bbox_inches='tight')  # Also save as PDF for high quality

print("Chart has been saved as 'profit_vs_changes.png' and 'profit_vs_changes.pdf' in your current directory!")


