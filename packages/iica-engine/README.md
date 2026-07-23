# Motor IICA

Paquete Python independiente que recibe el perfil del usuario, el vehículo, el
entorno y el mercado para producir una puntuación IICA explicable. El modelo
de dominio y el contrato público se definieron en la Fase 2; el algoritmo se
incorporó en la Fase 6.

No debe depender de interfaces, frameworks ni proveedores de almacenamiento.

## Contrato

Una implementación de `IicaEngine` recibe `EvaluationInput` y devuelve
`EvaluationResult`. Este último siempre contiene una única `Score` (0 a 100),
su clasificación y una explicación. Los objetos validan que país, ciudad y
moneda sean coherentes, y conservan las versiones de motor y datos necesarias
para reproducir cada cálculo.

`DeterministicIicaEngine` es la implementación inicial: pondera presupuesto,
seguridad, movilidad local, mercado, depreciación, uso, infraestructura y
garantía. Devuelve las influencias principales y no expone subíndices al
usuario. Sus pesos se centralizan en el código y están cubiertos por pruebas;
la calibración posterior se publicará mediante versiones del motor.
