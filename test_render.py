from jinja2 import Template

# Read the template
with open('kernels/asci_optimized_scrypt.cl.jinja', 'r') as f:
    template_content = f.read()

# Create the template
template = Template(template_content)

# Render the template
rendered = template.render()

# Save to a file
with open('test_rendered_kernel.cl', 'w') as f:
    f.write(rendered)

print('Kernel rendered successfully')