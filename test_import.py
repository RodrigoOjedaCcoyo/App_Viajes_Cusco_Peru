# test_import.py

# Usamos la notación simple que definimos en el Paso 2
from lead_controller import LeadController 
# También intenta esta importación si falla la primera
# from controllers.lead_controller import LeadController 

# Este código solo se ejecutará si la importación anterior NO falla
def run_test():
    print("¡Importación de LeadController exitosa!") 

if __name__ == '__main__':
    run_test()