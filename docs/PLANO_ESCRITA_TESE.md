# 📘 Plano Mestre Único de Escrita da Dissertação (Sprint de 2 Semanas)
**Título:** *A Model-Driven Framework for the Automated Generation and Synchronization of Dynamic Digital Twins in Manufacturing*  
**Autor:** TSGouveia | **Template:** NOVAthesis (LaTeX)  
**Stack Técnica do Projeto:**
- **Frontend / Modelação:** Python 3 (`conveyor_wizard.py` em PyQt6 + PyVista 3D + `basyx-python-sdk` + Xacro/URDF + Trimesh)
- **Middleware Semântico:** Eclipse BaSyx v2 em Docker (`aas-env:8081`, `aas-registry:8082`, `sm-registry:8083`, `aas-discovery:8084`, `mosquitto:1883` MQTT, `influxdb:8086`, `aas-ui:3000`, MongoDB)
- **Visualização & Simulação:** Unity 3D C# (`BaSyxManager.cs`, `Unity.Robotics.UrdfImporter` em runtime, `AASRuleEngine.cs`, `OperationMode.cs`, `DynamicProduct.cs`)
- **Hardware Industrial & Firmware:** Bancada Modular FMS / Tapetes Rolantes + Arduino Ethernet com FreeRTOS (`FMS_DT.ino`, tarefas concorrentes, filas e semáforos)

---

## 🧭 Metodologia: Estratégia "Inside-Out" com Divisão Inteligente do Hardware

### 🎯 Estratégia de Contacto com o Kit Físico:
1. **DIA 1 (Hoje - Seg): Sessão Fotográfica & Auditoria de Hardware**
   - Tirar todas as fotografias gerais e close-ups dos sensores, motores e placas.
   - Mapear a correspondência exata dos pinos de entrada e saída (`I` e `R` do `FMS_DT.ino`).
   - *Vantagem:* Em 45 minutos no laboratório ficas com todo o material visual e elétrico necessário para arrancar a escrita dos Capítulos 3 e 4 sem perder tempo a configurar setups de teste agora.
2. **DIA 8 (Próxima Segunda-feira): Hardware Test Day (Ensaios Experimentais & Logs)**
   - Correr os ensaios de sincronização em tempo real (Arduino $\leftrightarrow$ BaSyx $\leftrightarrow$ Unity).
   - Registar amostras de latência (REST vs MQTT) e tempos de setup.
   - *Vantagem:* Os testes são feitos no momento exato em que são precisos — logo antes de redigir o Capítulo 5 (Resultados).

### Sequência "Inside-Out" dos 14 Dias:
```
   DIA 1 (Hoje)        ──> FOTOS E MAPEAMENTO DO KIT FÍSICO (Desbloqueia a escrita)
                                      │
                                      ▼
   DIAS 2 a 5 (Sem. 1) ──> Capítulos 3 & 4 (Arquitetura e Implementação)
                           (Escrita acelerada apoiada nas fotos e diagramas)
                                      │
                                      ▼
   DIAS 6 e 7 (Fim S1) ──> Capítulo 2 (Estado da Arte & Tabela Comparativa)
                           (Aproveitar e consolidar a literatura já revista)
                                      │
                                      ▼
   DIA 8 (Próxima Seg) ──> HARDWARE TEST DAY (Ensaios, Latências e Logs no Lab)
                                      │
                                      ▼
   DIA 9 (Semana 2)    ──> Capítulo 5 (Caso de Estudo, Gráficos & Resultados)
                           (Tratar os dados recolhidos no Dia 8)
                                      │
                                      ▼
   DIAS 10 e 11        ──> Capítulos 1 & 6 (Introdução e Conclusões em Espelho)
                                      │
                                      ▼
   DIAS 12 a 14        ──> Front Matter, Abstract (PT/EN), Revisão e Submissão
```

---

# 🗺️ Mapeamento Exaustivo de Gráficos e Diagramas

| Ficheiro Sugerido | Capítulo & Secção | Tipo / Ferramenta | Conteúdo e Representação Visual | Relevância Técnica / Justificação |
| :--- | :--- | :--- | :--- | :--- |
| `fms_physical_bench.pdf` **[FOTOS DIA 1]** | Cap. 5 (§5.1) | Foto Anotada / Vetor | Fotografia de alta resolução da bancada física FMS anotando os postos, esteiras, sensores e atuadores. | Ancora a tese num ambiente experimental real e tangível. |
| `fms_sensor_actuator_details.pdf` **[FOTOS DIA 1]** | Cap. 5 (§5.1) | Painel de Fotos | Close-ups dos sensores óticos/indutivos, cancelas pneumáticas e ligação do Arduino Ethernet. | Comprova os detalhes de instrumentação física e robustez da montagem. |
| `architecture_global.pdf` **[CRIAR]** | Cap. 3 (§3.1) | Arquitetura / Draw.io | Visão global do sistema em 3 camadas: (1) Setup/Client Python, (2) Middleware BaSyx Docker, (3) Runtime Unity + FMS Hardware. | **O diagrama mais importante da tese.** Mostra o fluxo completo do pipeline e o desacoplamento de camadas. |
| `aas_metamodel_submodels.pdf` **[CRIAR]** | Cap. 3 (§3.2) | Esquema UML de Dados | Estrutura dos Submodelos concebidos: `TechnicalData`, `Geometry/URDF`, `VirtualPins` (I/O) e `ControlLogic`. | Demonstra a modelação semântica e como os ativos físicos são mapeados para o standard AAS. |
| `usecase_step1.pdf` a `step5.pdf` *(Já existem)* | Cap. 3 (§3.3) | Diagramas UML de Use Case | Os 5 passos do Wizard: (1) Modelo, (2) Transform/Comms, (3) Sensores, (4) Atuadores, (5) Build & Deploy. | Justifica a conceção funcional da ferramenta e a usabilidade guiada passo-a-passo. |
| `usecase_aux.pdf` *(Já existe)* | Cap. 3 (§3.4) | Diagrama UML de Use Case | Casos de uso auxiliares: CRUD de instâncias, Previsualização 3D de Layout e Editor de Regras. | Detalha a gestão do ciclo de vida dos ativos além da criação inicial. |
| `dual_mode_sequence.pdf` **[CRIAR]** | Cap. 3 (§3.5) | Diagrama de Sequência UML | Sequência de interação nos dois modos: (A) *Virtual Commissioning* (Unity Physics + Rule Engine) vs (B) *Digital Twin* (Arduino Hardware + REST Sync). | Explica tecnicamente o que muda no fluxo quando a bancada física está ligada ou em modo de simulação prévia. |
| `wizard_ui_screenshots.pdf` **[CRIAR]** | Cap. 4 (§4.1) | Grelha de Screenshots | Janela do `conveyor_wizard.py`: Visualizador 3D (PyVista), Configuração de I/O, Editor de Regras. | Prova visual da implementação real da interface gráfica e usabilidade. |
| `basyx_docker_topology.pdf` **[CRIAR]** | Cap. 4 (§4.2) | Diagrama de Rede / Docker | Topologia dos contentores: `aas-env`, `aas-registry`, `sm-registry`, `mosquitto`, `influxdb`, `aas-ui`. | Descreve a infraestrutura de microsserviços do middleware industrial e portas expostas. |
| `unity_scene_hierarchy.pdf` **[CRIAR]** | Cap. 4 (§4.3) | Screenshot + Esquema | Unity em execução: Peças dinâmicas (`DynamicProduct.cs`), tapetes gerados por URDF e UI de controlo. | Mostra a geração procedural e a física do Digital Twin no motor de jogo sem modelos hardcoded. |
| `arduino_freertos_schema.pdf` **[CRIAR]** | Cap. 4 (§4.4) | Esquema de Blocos | Arquitetura do firmware `FMS_DT.ino`: Tarefas FreeRTOS, Filas, Mutexes, EthernetServer e I/O. | Demonstra rigor técnico no desenvolvimento do firmware embedded em tempo real. |
| `i4.0_history.pdf` *(Já existe)* | Cap. 2 (§2.1) | Ilustração Conceitual | Da Indústria 1.0 (Vapor) à 4.0 (CPS) e 5.0 (Centrado no Humano / Resiliência). | Contextualiza a evolução histórica e a necessidade de flexibilidade industrial. |
| `digital_twin_flow.pdf` *(Já existe)* | Cap. 2 (§2.2) | Diagrama de Blocos | Comparação entre Digital Model (manual), Digital Shadow (unidirecional) e Digital Twin (bidirecional). | Clarifica formalmente o conceito exato de Digital Twin usado na tese. |
| `rami.pdf` *(Já existe)* | Cap. 2 (§2.3) | Arquitetura 3D | Modelo RAMI 4.0 (Camadas, Ciclo de Vida, Níveis de Hierarquia). | Fundamenta a normalização e onde o Asset Administration Shell se insere. |
| `AAS_introduction.pdf` *(Já existe)* | Cap. 2 (§2.4) | Diagrama Estrutural | Estrutura interna do AAS: Header, Body, Submodels, Submodel Elements, Views. | Mostra a anatomia do padrão base que o Wizard vai instanciar e preencher. |
| `AML_Architecture.pdf` *(Já existe)* | Cap. 2 (§2.5) | Diagrama de Árvore | Hierarquia do AutomationML (SystemUnitClasses, InstanceHierarchy, RoleClasses). | Explica a origem dos dados estáticos de engenharia da fábrica. |
| `state_of_art_comparison.pdf` / Tabela | Cap. 2 (§2.6) | Tabela Comparativa | Tabela comparando abordagens da literatura (Standards, Automação, 3D Runtime, Bidirecional). | Demonstra categoricamente a lacuna científica que a tua tese vem preencher. |
| `sync_latency_boxplot.pdf` **[TESTES DIA 8]** | Cap. 5 (§5.3) | Boxplot / Python | Latência de sincronização (ms) medida na bancada entre o trigger real e a atualização no Unity/BaSyx. | Avalia o desempenho temporal e a viabilidade da sincronização em tempo real. |
| `manual_vs_wizard_time.pdf` **[TESTES DIA 8]** | Cap. 5 (§5.2) | Gráfico de Barras (Matplotlib) | Tempo de engenharia (minutos): Criação manual de AASX vs Configuração guiada pelo Wizard. | Prova quantitativa da redução de esforço de engenharia trazida pela tese. |
| `traffic_overhead_analysis.pdf` **[TESTES DIA 8]** | Cap. 5 (§5.4) | Gráfico de Barras / Área | Consumo de largura de banda / pedidos por segundo em função do número de módulos ativos. | Avalia a escalabilidade da solução quando a linha de produção cresce. |

---

# 📅 Cronograma Diário e Checklist Hierárquica (14 Dias)

---

## 📍 DIA 1 (Hoje - Seg): FOTOS E MAPEAMENTO DO KIT FÍSICO
*Objetivo Único: Obter todas as imagens reais de alta qualidade e mapear os pinos elétricos para começar a escrever imediatamente sem atritos.*

### [ ] Tarefa 1: Sessão Fotográfica Completa da Bancada FMS
- [ ] Sub-tarefa 1.1: Fotografia Geral Panorâmica (`fms_physical_bench.pdf`)
  - [ ] [Sub-sub-tarefa 1.1.1] Limpar a bancada e garantir boa iluminação sem reflexos fortes.
  - [ ] [Sub-sub-tarefa 1.1.2] Tirar 3 a 5 fotos gerais de diferentes ângulos (perspetiva isométrica, vista superior e frontal).
  - [ ] [Sub-sub-tarefa 1.1.3] Selecionar a melhor fotografia para adicionar setas anotadas no LaTeX.
- [ ] Sub-tarefa 1.2: Close-ups dos Componentes Físicos (`fms_sensor_actuator_details.pdf`)
  - [ ] [Sub-sub-tarefa 1.2.1] Foto dos sensores óticos/reflexivos de barreira.
  - [ ] [Sub-sub-tarefa 1.2.2] Foto dos sensores indutivos de presença de palete/metal.
  - [ ] [Sub-sub-tarefa 1.2.3] Foto dos motores das esteiras e respetivos relés de comando.
  - [ ] [Sub-sub-tarefa 1.2.4] Foto das cancelas pneumáticas/mecânicas (stoppers e diverters).
  - [ ] [Sub-sub-tarefa 1.2.5] Foto do braço robótico (se acoplado à célula).
  - [ ] [Sub-sub-tarefa 1.2.6] Foto da caixa de controlo com o Arduino Mega + Ethernet Shield e cablagens.
- [ ] Sub-tarefa 1.3: Gravação de Vídeo / Sequência
  - [ ] [Sub-sub-tarefa 1.3.1] Gravar um clipe de 30-60s com uma peça a circular para apoio à tese/defesa.

### [ ] Tarefa 2: Auditoria e Mapeamento de Hardware (Pinouts)
- [ ] Sub-tarefa 2.1: Mapeamento de Entradas (Sensores $\rightarrow$ Pinos Arduino)
  - [ ] [Sub-sub-tarefa 2.1.1] Confrontar o array `porto_I[3][6]` do `FMS_DT.ino` com os sensores reais na bancada.
  - [ ] [Sub-sub-tarefa 2.1.2] Registar a correspondência física: que pino (`I0_0` a `I2_5`) é qual sensor.
- [ ] Sub-tarefa 2.2: Mapeamento de Saídas (Atuadores $\rightarrow$ Relés Arduino)
  - [ ] [Sub-sub-tarefa 2.2.1] Confrontar o array `porto_R[3][9]` com as esteiras e cancelas.
  - [ ] [Sub-sub-tarefa 2.2.2] Registar a correspondência física de cada relé (`R0_0` a `R2_8`).
- [ ] **Desfecho do Dia 1:** Guardar as fotos na pasta `Documentos/5-Figures/` e os apontamentos de pinos no bloco de notas do tracker. Missão de hoje no laboratório concluída com sucesso!

---

## SEMANA 1 (Dias 2 a 7): Redação dos Capítulos 3, 4 e 2

### 📍 DIA 2 (Terça-feira): Capítulo 3 – Arquitetura Global e Metamodelo AAS ([chapter3.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter3.tex))
- [ ] **Tarefa 3: Diagrama de Arquitetura Global e Camadas**
  - [ ] Sub-tarefa 3.1: Desenhar no Draw.io o esquema em 3 camadas `architecture_global.pdf` (Client Python Wizard, Middleware BaSyx Docker, Unity + Arduino FMS).
  - [ ] Sub-tarefa 3.2: Exportar em PDF vetorial para `Documentos/5-Figures/architecture_global.pdf`.
  - [ ] Sub-tarefa 3.3: Redigir a Secção 3.1 apresentando a divisão concetual e o desacoplamento do sistema.
- [ ] **Tarefa 4: Metamodelo e Submodelos AAS**
  - [ ] Sub-tarefa 4.1: Criar o diagrama UML `aas_metamodel_submodels.pdf` (`TechnicalData`, `Geometry/URDF`, `VirtualPins`, `ControlLogic`).
  - [ ] Sub-tarefa 4.2: Redigir a Secção 3.2 justificando a semântica de cada submodelo.

---

### 📍 DIA 3 (Quarta-feira): Capítulo 3 – Pipeline de 5 Passos e Modo Duplo ([chapter3.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter3.tex))
- [ ] **Tarefa 5: O Pipeline Interativo de 5 Passos**
  - [ ] Sub-tarefa 5.1: Redigir Secção 3.3.1 (Step 1: Model Selection & Geometric Parsing) referenciando `usecase_step1.pdf`.
  - [ ] Sub-tarefa 5.2: Redigir Secção 3.3.2 (Step 2: System Info, Communication & Spatial Transform) referenciando `usecase_step2.pdf`.
  - [ ] Sub-tarefa 5.3: Redigir Secções 3.3.3 e 3.3.4 (Steps 3 & 4: Sensors & Actuators I/O Mapping) referenciando `usecase_step3.pdf` e `usecase_step4.pdf`.
  - [ ] Sub-tarefa 5.4: Redigir Secção 3.3.5 (Step 5: Review, Build & Deployment) referenciando `usecase_step5.pdf`.
- [ ] **Tarefa 6: Operações Auxiliares e Modo Duplo (*Virtual Commissioning* vs *Digital Twin*)**
  - [ ] Sub-tarefa 6.1: Redigir Secção 3.4 (Operações Auxiliares: CRUD, Layout Preview, Rule Engine) referenciando `usecase_aux.pdf`.
  - [ ] Sub-tarefa 6.2: Criar o diagrama de sequência `dual_mode_sequence.pdf` e redigir a Secção 3.5 explicando o chaveamento entre física virtual e hardware real.

---

### 📍 DIA 4 (Quinta-feira): Capítulo 4 – Implementação Python e Docker ([chapter4.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter4.tex))
- [ ] **Tarefa 7: Implementação do AAS Client (`conveyor_wizard.py`)**
  - [ ] Sub-tarefa 7.1: Montar o painel de capturas `wizard_ui_screenshots.pdf` (PyVista 3D, tabelas I/O e deploy).
  - [ ] Sub-tarefa 7.2: Redigir a Secção 4.1 detalhando a arquitetura em Python (`XacroResolver`, `AssetManager`, `AASRulesEditorDialog`) e incluir listing de código da criação do AASX.
- [ ] **Tarefa 8: Middleware Industrial em Docker (`AAS Docker`)**
  - [ ] Sub-tarefa 8.1: Criar diagrama `basyx_docker_topology.pdf` e redigir Secção 4.2 sobre os microsserviços (`aas-env:8081`, `aas-registry:8082`, `mosquitto:1883`, `influxdb:8086`, `aas-ui:3000`).

---

### 📍 DIA 5 (Sexta-feira): Capítulo 4 – Implementação Unity e Arduino ([chapter4.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter4.tex))
- [ ] **Tarefa 9: Cliente de Visualização e Simulação em Unity (`DT Unity`)**
  - [ ] Sub-tarefa 9.1: Captura da cena Unity (`unity_scene_hierarchy.pdf`) e redação da Secção 4.3 sobre o `BaSyxManager.cs` (descoberta periódica, download do URDF, instanciação procedural), `AASRuleEngine.cs` e `DynamicProduct.cs`.
- [ ] **Tarefa 10: Firmware Embedded Arduino (`FMS_DT.ino`)**
  - [ ] Sub-tarefa 10.1: Criar o esquema `arduino_freertos_schema.pdf` (tarefas de sensores, relés, EthernetServer e mutexes).
  - [ ] Sub-tarefa 10.2: Inserir a tabela com o mapeamento físico de pinos (Portos I e R) que levantaste no Dia 1.

---

### 📍 DIA 6 (Sábado): Capítulo 2 – Estado da Arte (Conceitos & Normas) ([chapter2.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter2.tex))
- [ ] **Tarefa 11: Revisão dos Fundamentos Teóricos Existentes**
  - [ ] Sub-tarefa 11.1: Rever Secção 2.1 (I4.0/I5.0 e CPS) referenciando `i4.0_history.pdf`.
  - [ ] Sub-tarefa 11.2: Rever Secção 2.2 (Taxonomia de Digital Twins) referenciando `digital_model_flow.pdf`, `digital_shadow_flow.pdf` e `digital_twin_flow.pdf`.
  - [ ] Sub-tarefa 11.3: Rever Secção 2.3 (RAMI 4.0 e BaSyx AAS) referenciando `rami.pdf` e `AAS_introduction.pdf`.
  - [ ] Sub-tarefa 11.4: Rever Secção 2.4 (AutomationML e modelos de engenharia) referenciando `AML_Architecture.pdf`.

---

### 📍 DIA 7 (Domingo): Capítulo 2 – Game Engines & Tabela Comparativa ([chapter2.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter2.tex))
- [ ] **Tarefa 12: Game Engines e Síntese da Literatura**
  - [ ] Sub-tarefa 12.1: Escrever secção sobre o papel do Unity vs simuladores fechados.
  - [ ] Sub-tarefa 12.2: Construir a Tabela Comparativa de Trabalhos Relacionados (6 artigos de 2020–2026 comparados com a tua tese).
  - [ ] Sub-tarefa 12.3: Escrever a secção "Gaps Identified" preparando a transição lógica para a tua solução.
- [ ] **Tarefa 13: Checkpoint da Semana 1**
  - [ ] Sub-tarefa 13.1: Compilar [thesis.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/thesis.tex) e verificar a consistência dos Capítulos 2, 3 e 4.
  - [ ] Sub-tarefa 13.2: Fazer commit no Git (`git commit -m "Semana 1 concluida: Caps 2, 3 e 4 fechados"`).

---

## SEMANA 2 (Dias 8 a 14): Testes, Resultados, Enquadramento e Fecho

### 📍 DIA 8 (Segunda-feira): HARDWARE TEST DAY NO LAB (Ensaios Experimentais e Logs)
*Objetivo: Com a bancada física ligada, recolher 100% dos dados quantitativos para alimentar o Capítulo 5.*

- [ ] **Tarefa 14: Ensaio de Sincronização em Tempo Real (Hardware $\leftrightarrow$ BaSyx $\leftrightarrow$ Unity)**
  - [ ] Sub-tarefa 14.1: Ligar Docker BaSyx, cabo Ethernet ao Arduino e Unity no modo `DigitalTwin`.
  - [ ] Sub-tarefa 14.2: Fazer 30 a 50 passagens de peças na esteira e guardar o log da consola com timestamps dos eventos de sensor.
- [ ] **Tarefa 15: Ensaio Comparativo de Latência (REST vs MQTT)**
  - [ ] Sub-tarefa 15.1: Medir o tempo de resposta entre o sensor físico e a atualização no Unity via REST (`http://localhost:8081`).
  - [ ] Sub-tarefa 15.2: Registar tempos via telemetria MQTT ou socket direto.
  - [ ] Sub-tarefa 15.3: Guardar os valores no ficheiro `scratch/latencias_teste.csv`.
- [ ] **Tarefa 16: Cronometragem de Configuração (Setup Time)**
  - [ ] Sub-tarefa 16.1: Cronometrar o tempo de reconfiguração de um módulo usando o `conveyor_wizard.py` (Passo 1 ao Passo 5).
  - [ ] Sub-tarefa 16.2: Registar o valor para confrontar com o método manual oficial (AASX Package Explorer).

---

### 📍 DIA 9 (Terça-feira): Capítulo 5 – Caso de Estudo, Resultados e Discussão ([chapter5.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter5.tex))
- [ ] **Tarefa 17: Cenário Experimental e Caracterização da Bancada**
  - [ ] Sub-tarefa 17.1: Inserir a foto anotada `fms_physical_bench.pdf` e o painel `fms_sensor_actuator_details.pdf` (tiradas no Dia 1).
  - [ ] Sub-tarefa 17.2: Redigir a Secção 5.1 caracterizando a célula modular, o fluxo de paletes e os postos de paragem.
- [ ] **Tarefa 18: Gráficos de Resultados e Análise**
  - [ ] Sub-tarefa 18.1: Gerar o gráfico de barras `manual_vs_wizard_time.pdf` (Matplotlib) e redigir a Secção 5.2.
  - [ ] Sub-tarefa 18.2: Gerar o boxplot `sync_latency_boxplot.pdf` a partir do CSV do Dia 8 e redigir a Secção 5.3.
- [ ] **Tarefa 19: Discussão Crítica e Limitações**
  - [ ] Sub-tarefa 19.1: Redigir a Secção 5.4 discutindo os limites de desempenho da física no Unity e escalabilidade de rede.

---

### 📍 DIA 10 (Quarta-feira): Capítulo 1 – Introdução & Objetivos ([chapter1.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter1.tex))
- [ ] **Tarefa 20: Redação Final da Introdução**
  - [ ] Sub-tarefa 20.1: Background e Motivação alinhados com a experiência prática da bancada FMS.
  - [ ] Sub-tarefa 20.2: Definição do Problema e Enunciação dos 4 Objetivos Específicos.
  - [ ] Sub-tarefa 20.3: Listar as 4 Contribuições Principais e redigir o Guia da Dissertação (*Thesis Outline*).

---

### 📍 DIA 11 (Quinta-feira): Capítulo 6 – Conclusões & Trabalho Futuro ([chapter6.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/2-MainMatter/chapter6.tex))
- [ ] **Tarefa 21: Conclusões (O Espelho da Introdução)**
  - [ ] Sub-tarefa 21.1: Avaliação do cumprimento de cada objetivo do Capítulo 1 com base nos resultados do Capítulo 5.
  - [ ] Sub-tarefa 21.2: Síntese do impacto prático e trabalho futuro (LLMs industriais com `nvidia_llm.pdf`, Realidade Aumentada e OPC UA).

---

### 📍 DIA 12 (Sexta-feira): Front Matter, Resumos e Acrónimos
- [ ] **Tarefa 22: Elementos Pré-Textuais**
  - [ ] Sub-tarefa 22.1: Redigir Resumo em Português ([abstract-pt.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/1-FrontMatter/abstract-pt.tex)) em 4 parágrafos canónicos + 6 Palavras-Chave.
  - [ ] Sub-tarefa 22.2: Redigir Abstract em Inglês ([abstract-en.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/1-FrontMatter/abstract-en.tex)) + 6 Keywords.
  - [ ] Sub-tarefa 22.3: Escrever Agradecimentos ([acknowledgements.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/1-FrontMatter/acknowledgements.tex)).
  - [ ] Sub-tarefa 22.4: Preencher Declaração de Uso de IA ([aidisclosure.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/1-FrontMatter/aidisclosure.tex)) e Capa ([3_cover.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/0-Config/3_cover.tex)).
  - [ ] Sub-tarefa 22.5: Auditoria de Acrónimos em [acronyms.tex](file:///C:/Users/LazyT/Desktop/Tese/Documentos/1-FrontMatter/acronyms.tex).

---

### 📍 DIA 13 (Sábado): Auditoria Cruzada e Correção Gramatical
- [ ] **Tarefa 23: Deteção e Resolução de Erros Globais**
  - [ ] Sub-tarefa 23.1: Resolver referências quebradas (`??` e `[?]`).
  - [ ] Sub-tarefa 23.2: Garantir que todas as figuras têm `\caption`, `\label` e são citadas no texto com `\Cref{...}`.
  - [ ] Sub-tarefa 23.3: Revisão ortográfica e de estilo em Inglês técnico.

---

### 📍 DIA 14 (Domingo): Formatação Final e Congelamento (Submission Freeze)
- [ ] **Tarefa 24: Compilação Limpa e Geração do PDF Final**
  - [ ] Sub-tarefa 24.1: Limpeza de ficheiros temporários (`.aux`, `.bbl`, etc.).
  - [ ] Sub-tarefa 24.2: Compilação completa (LaTeX + Biber + Glossaries + 2x LaTeX).
  - [ ] Sub-tarefa 24.3: Inspecionar visualmente o documento página a página.
  - [ ] Sub-tarefa 24.4: Gerar `Tese_Mestrado_TSGouveia_FINAL.pdf` e criar a tag no Git (`v1.0-submission`).
