from jinja2 import Template

# Read the template
with open('kernels/scrypt_core.cl.jinja', 'r') as f:
    template_content = f.read()

# Create the template
template = Template(template_content)

# Render the template
rendered = template.render()

# Save to a file
with open('test_scrypt_core_rendered.cl', 'w') as f:
    f.write(rendered)

print('Scrypt core kernel rendered successfully')