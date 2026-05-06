# Low-Level Design – Fullstack Design for AdaLead

## 🔍 Definitions and Acronyms

- **API**: Application Programming Interface.
- **TDD**: Test Driven Development.
- **HTTP**: Hypertext Transfer Protocol.
- **CRUD**: Create (*HTTP POST Method*), Read (*HTTP GET Method*), Update (*HTTP PUT or PATCH Methods*), Delete (*HTTP DELETE Method*).
    - **POST**: HTTP method for sending data to the server.
    - **GET**: HTTP method for retrieving data from the server.
    - **PUT**: HTTP method for editing all data from a server's entity.
    - **PATCH**: HTTP method for editing a portion of the data from a server's entity.
    - **DELETE**: HTTP method for deleting data from the server.
    - **OPTIONS**: HTTP method for showing all available methods on an endpoint.
- **IoT**: Internet of Things.
- **ESP32**: Microcontroller that has a WiFi and BLE (Bluetooth Low Energy) modules for wireless conection.
- **IoT Wheel (Enerdrais)**: Electrical energy generation front bycicle wheel that has an ESP32 microcontroller to gather all energy data generated to further trasmit it to a remote database.
- **Voltage (V)**: Potential force that makes electricity move [ Volts ].
- **Current (A)**: Electric current is the flow of electricity through a wire [ Amperes ].
- **Power (W)**: Is the measure of how much energy electricity can be delivered every second [Watts = Joules/second = V*A].
- **Joules (J)**: Is the unit measure of energy, which can be cinetical, potential or electrical [ Joules ].

---

## Problem to Solve (Abstract/Overview)

The goal is to build and develop the frontend and backend architecture of a system from scratch, taking into account the business requirements as follows:

&nbsp;
**Backend:**

- The company Enerdrais needs a system that allows an IoT device to upload energy generation data, which includes Voltage, Current, and Power, so that anyone worldwide can see that data in a black powered off world animation that they can interact with. Another very important requierement is that a backend API system is enabled to share the following data:
  - Location of the wheel.
  - Timestamp (date and time) of when each route using the wheel started and when it ended.
  - Voltage, Amperage and Power.
  - Maybe we could feed of another API or fill out a database that gives most updated energy data worldly by region, to assign an energy number `(Watts = Voltage*Current)` to each strategic point.

&nbsp;
**Frontend:**

- The company enerdrais wishes to display this energy information in a map that gets inspired by these designs, but showing the world in a black color: #000000, and showing the energyzed parts as a gold color: #eec53eff, also displaying other parts of the frontend like the lines between the countries in the red logo color: #E90013. Another requierement is that we need to zoom on this world map to see the areas where Enerdrais is located and see a graph of the voltage and amperage vs time that is being generated per wheel in real time. In the img folder have uploaded all the different versions of the logos and some other frontend proposals. If we could add some bolt animations to the world map that would be amazing, but it's a plus, if it can't be done, no issues.
  - We could be able to fetch the world view frontend data from one of these sources, or at least take them as inspiration:
    - https://www.mappicker.com/
    - https://earth3dmap.com/

Note: The Enerdrais company primarily will have its users in America (Mexico City and Guadalajara to start), where its largest market is, but they will also intent to have sales (show data) in U.S., Europe, and India to gather investor capital.

![Enerdrais_Proposal_Globe_1](img/frontend_proposals/Enerdrais_Proposal_Globe_1.jpg)

---

## 🎯 Objectives Minimum Viable Product for Enerdrais

### Services (Minimum Viable Product Requirements)
1. Dispositivo inalámbrico y carcasa del brazalete.
2. Batería de dispositivo incluida dentro del brazalete.
3. Circuito Impreso (PCB) que integre el sistema embebido ESP32 y sus sensores.
4. Connection from the API with the ESP32 as a subscriber (through Lambda and serverless) with a mechanism for avoiding data leaks.
5. El usuario envía alertas con un botón de pánico digital o (agitando), con capacidades online y offline. Si algún usuario de AdaLead que tenga otro brazalete se encuentra en un rango cercano, recibirá dicha alerta.
6. Integración de sensor giroscopio.
7. Investigar y escoger radiofrecuencia de seguridad para el caso donde no se tiene conexión web del celular al que esté conectado el ESP32.
8. El proceso de AUTH (Autenticación) se realiza a través de dispositivos ESP32 (para asegurarnos que nadie fuera de la programación de AdaLead pueda usar nuestra API a menos que tenga un brazalete).
9. La alerta se comparte con los brazaletes AdaLead cercanos, al mismo tiempo que se alimenta una base de datos geoespacial de cartografía que denota los focos de violencia.

### Features (May or may not change based upon conditions)
1. Enviar timestamps (tiempo y hora) de cuando se emite alguna alerta con el botón de pánico.
2. Identificación de patrones de sucesos antes de un evento de violencia letal o extrema (investigación de APIs externas como [ushahidi.com](ushahidi.com), [API ushahidi](https://docs.ushahidi.com/v3-ushahidi-platform-rest-api-documentation) y [API ushahidi](http://preview.ushahidi.com/platform/develop/api/index.html)).
3. Los análisis basados en IA detectan pautas de violencia y emiten alertas tempranas.
4. Escaneo cara a cara de códigos personales encriptados (en blockchain??) ayuda a los usuarios a crear redes de confianza y respuesta rápida. Solamente personas que estén en persona se deben poder integrar a mi red, no me sirve que alguien de la India se agregue a mi red si tengo el siniestro en México.
5. Formulario de integración de datos de red de confianza, incuido teléfono y redes sociales.
6. Self defense taser.

### Stakeholders

- **Mechatronic Product:** Diego Cervantes.
- **Fullstack Engineering:** Mauricio Raini.
- **Manufacture Engineering:** Luis Gerardo Valdez.
- **Marketing and Social Media:** Mauricio Cervera.
- **Possible Investors:** Bevisioneers (a Mercedes Benz Fellowship), and the Estonia, Finland or Switzerland government.
- *Editors (upload content to the system):* Initially from Mexico.
- *End Users / Readers (consume content):* Bevisioneers, Estonia, Finland, Switzerland, Germany, and India.

---

## 💭 Assumptions

- Only editors (IoT Enerdrais energy generation wheels) will require authentication and write access.
- Users do not need to register to read the global energy data.
- Editors are primarily based in Mexico, because it will be the first region that Enerdrais will get implemented.
- Most viewers are located in North America and Europe, with lesser presence in Asia.

---

## 🚧 Limitations and Unknowns

This section lists known limitations, either in resources or knowledge, and should be presented in quantifiable terms.
- There could already exist an API that gathers energy crisis information categoryzed by country or region we can use to show the energy data in the world map.
- Traffic estimates are based on current known markets; rapid growth may require load balancing or vertical/horizontal scaling.
- API calls for uploading energy data (POST) must stay within 300ms latency limits.
- API calls for reading energy data (GET) must stay under 100ms latency.

---

## ✅ Project Scope (Included)

- Some REST API endpoints examples we could use for uploading generated energy data in real time are: IoT energy posted to the database (`POST /energy-generated`), energy global energy crisis indicators (`GET /energy-crisis-regions`), enerdrais region locations and energy levels (`GET /enerdrais-regions`), etc.
- Authentication and access control for IoT uploader devices.
- Storage and retrieval of energy data.
- Preparedness for geographic distribution in read operations.
- Backend deployed, with public API ready to consume.
- World map animation with we can interact deployed and published.

### ❌ Out of Scope

- Authentication for readers.

## 🧠 Proposal

### 🏗️ General Architecture


---

### API Endpoints

| Method | Endpoint                   | Description                                                                                   | Requires Authentication  |
|--------|----------------------------|-----------------------------------------------------------------------------------------------|--------------------------|
| POST   | /wheel-energy              | Upload of Voltage, Current, Power, location, Initial and finish time of energy generation.    | ✅ Yes                   |
| GET    | /region-energy             | Integration of a possible external API to gather energy (Watts) data per region in the world. | ❌ No                    |
| GET    | /energy-crisis-regions     | Retrieve world energy situation data.                                                         | ❌ No                    |
| GET    | /enerdrais-regions         | Retrieve all enerdrais locations and energy indicators per region.                            | ❌ No                    |
| OPTIONS| OTHER ENDPOINTS WE THINK OF| OTHER RELEVANT ENERGY INFORMATION WE CAN THINK OF...                                          | ❓ Maybe                 |

---

#### 📊 Data Models (SQL)

This section will describe entities, relationships, JSONs, tables, ER diagrams, etc., related to the system's database.


#### Test Plan (TDD)
Along with architecture diagrams and data models, it is also worthwhile to design a test plan to validate certain use cases, simulating normal usage of the application and preventing failure cases, ensuring everything works before deploying to the cloud.

### ✅ Use Cases
These are developed through iterations with the client, describing usage examples for clarity between both parties.
First TDD test case implemented: Upload energy generatd data from the Enerdrais IoT wheel device to the database and simulate a visitor reading the energy data, which is categorized by location and shown on the black map, showing in its corresponding location, glowing in gold color depending on the level of energy per region.

### ❌ Unsupported Use Cases
These are also developed through iterations with the client, describing usage examples for clarity.


### Continuous Integration (CI/CD)
This section includes pipeline diagrams describing the process of feature implementation and bug fixes when these are pushed to the system, running tests when changes are submitted to GitHub. It outlines the integration (merge) flow between branches and assigns each to the development process:


---

### System Components


### 💸 Cost Considerations

