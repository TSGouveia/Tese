# Guia de Movimentação e Sensores

## 1. Como fazer translação/rotação
No teu JSON do AAS (Submodelo de Comportamento), define um elemento para o teu Atuador.

### Exemplo: Translação Contínua (Empurrador)
- **Component**: Nome do objeto ou Empty no Blender.
- **Type**: `TranslateContinuous`
- **Parameters**:
    - `AxisZ`: 1 (direção do movimento)
    - `Speed`: 0.5 (velocidade)
    - `StopSensorComponent`: "Nome_Do_Teu_Sensor" (opcional)

### Exemplo: Rotação (Braço)
- **Type**: `RotateContinuous` ou `RotateHinge` (para ângulos fixos).

## 2. Sensores Invisíveis
Para teres uma "trigger zone" que não se vê na Unity:
No Submodelo do Sensor, adiciona o parâmetro:
- `Visible`: `false`

## 3. Organização no Blender
- Usa **Empties** para agrupar objetos caóticos.
- O script mexe o objeto que deres o nome; se esse objeto tiver filhos, eles vão todos atrás.