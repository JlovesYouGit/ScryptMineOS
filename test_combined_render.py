from jinja2 import Template

# Read both templates
with open('kernels/scrypt_core.cl.jinja', 'r') as f:
    scrypt_core_content = f.read()

with open('kernels/asic_optimized_scrypt.cl.jinja', 'r') as f:
    asic_content = f.read()

# Create templates
scrypt_core_template = Template(scrypt_core_content)
asic_template = Template(asic_content)

# Render both templates
scrypt_core_rendered = scrypt_core_template.render()
asic_rendered = asic_template.render()

# Combine the rendered content
combined_content = scrypt_core_rendered + "\n\n" + asic_rendered

# Save to a file
with open('test_combined_rendered.cl', 'w') as f:
    f.write(combined_content)

print('Combined kernel rendered successfully')