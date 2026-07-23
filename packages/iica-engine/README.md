# Motor IICA

Paquete Python independiente que recibe el perfil del usuario, el vehículo, el
entorno y el mercado para producir una puntuación IICA explicable. El modelo
de dominio y el contrato público se definieron en la Fase 2; el algoritmo se
incorporará en la Fase 6.

No debe depender de interfaces, frameworks ni proveedores de almacenamiento.

## Contrato

Una implementación de `IicaEngine` recibe `EvaluationInput` y devuelve
`EvaluationResult`. Este último siempre contiene una única `Score` (0 a 100),
su clasificación y una explicación. Los objetos validan que país, ciudad y
moneda sean coherentes, y conservan las versiones de motor y datos necesarias
para reproducir cada cálculo.
