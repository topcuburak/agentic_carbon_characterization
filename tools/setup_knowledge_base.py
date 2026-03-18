"""
Sets up the knowledge base for search and web_lookup tools.
Creates JSON files with factual data for multi-hop QA and research tasks.
Run standalone: python -m tools.setup_knowledge_base
"""

import json
import os
from config import KNOWLEDGE_BASE_DIR


def create_knowledge_base():
    """Create the knowledge base files."""
    os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
    _create_facts_db()
    _create_web_cache()
    print(f"Knowledge base created at {KNOWLEDGE_BASE_DIR}")


def _create_facts_db():
    """Create the searchable facts database for the search tool."""
    facts = [
        # Countries & Geography
        {"title": "Brazil", "content": "Brazil is the largest country in South America by area (8,515,767 km²). GDP: $2.13 trillion USD (2024). Population: 216 million. Capital: Brasília."},
        {"title": "Argentina", "content": "Argentina is the second largest country in South America by area (2,780,400 km²). GDP: $621 billion USD (2024). Population: 46 million. Capital: Buenos Aires."},
        {"title": "Peru", "content": "Peru is the third largest country in South America by area (1,285,216 km²). GDP: $268 billion USD (2024). Population: 34 million. Capital: Lima."},
        {"title": "Colombia", "content": "Colombia has an area of 1,141,748 km². GDP: $363 billion USD (2024). Population: 52 million. Capital: Bogotá."},
        {"title": "France", "content": "France has an area of 643,801 km². Population: 68 million. Capital: Paris. It is the largest EU member state by area. France shares borders with Belgium (620 km), Luxembourg (73 km), Germany (418 km), Switzerland (573 km), Italy (515 km), Spain (623 km), Andorra (56.6 km), and Monaco (4.4 km). Total border length: ~2,883 km."},
        {"title": "European Union area", "content": "The European Union has a total area of approximately 4,233,262 km² (as of 2024, 27 member states). France is the largest member by area at 643,801 km²."},
        {"title": "Volga River", "content": "The Volga is the longest river in Europe at 3,531 km. It flows through Russia and empties into the Caspian Sea. The Caspian Sea borders Russia, Kazakhstan, Turkmenistan, Iran, and Azerbaijan."},
        {"title": "Russia", "content": "Russia has an area of 17,098,242 km². Population: 144 million. Population density: approximately 8.4 people per km². The Volga River, Europe's longest, flows through Russia into the Caspian Sea."},
        {"title": "Capital cities by elevation", "content": "La Paz, Bolivia is the highest capital city in the world at approximately 3,640 meters above sea level. Baku, Azerbaijan is often cited as the lowest capital city at approximately 28 meters below sea level."},

        # Animals
        {"title": "African elephant", "content": "The African bush elephant is the heaviest land mammal, weighing up to 6,000-7,000 kg (average adult male ~6,000 kg)."},
        {"title": "Common ostrich", "content": "The common ostrich is the heaviest living bird, weighing up to 100-160 kg (average adult male ~130 kg). It is also the tallest living bird."},

        # Science
        {"title": "Marie Curie discoveries", "content": "Marie Curie discovered two elements: Polonium (atomic number 84) in 1898 and Radium (atomic number 88) in 1898. She won Nobel Prizes in both Physics (1903) and Chemistry (1911)."},
        {"title": "Polonium", "content": "Polonium is a chemical element with symbol Po and atomic number 84. Discovered by Marie and Pierre Curie in 1898."},
        {"title": "Radium", "content": "Radium is a chemical element with symbol Ra and atomic number 88. Discovered by Marie and Pierre Curie in 1898."},
        {"title": "Alfred Nobel", "content": "Alfred Nobel was the inventor of dynamite. He was born in Stockholm, Sweden on October 21, 1833. He established the Nobel Prizes in his will."},
        {"title": "Nobel Prize Physics laureates from Stockholm", "content": "Notable Nobel Prize in Physics laureates born in Stockholm include Hannes Alfvén (1970, born in Norrköping, not Stockholm) and Manne Siegbahn (1924, born in Örebro). Svante Arrhenius (Chemistry, 1903) was born near Uppsala. Kai Siegbahn (Physics, 1981) was born in Lund."},

        # US Presidents
        {"title": "US Presidents born in Virginia", "content": "Eight US presidents were born in Virginia: George Washington (1732), Thomas Jefferson (1743), James Madison (1751), James Monroe (1758), William Henry Harrison (1773), John Tyler (1790), Zachary Taylor (1784), and Woodrow Wilson (1856). The first was Washington (1732) and the last was Wilson (1856), a span of 124 years."},

        # Solar System
        {"title": "Saturn moons", "content": "Saturn has the most confirmed moons of any planet in the solar system with 146 known moons (as of 2024). Earth has 1 moon. The ratio is 146:1."},
        {"title": "Jupiter moons", "content": "Jupiter has 95 confirmed moons as of 2024. Its largest moons are the four Galilean moons: Io, Europa, Ganymede, and Callisto."},

        # Technology
        {"title": "PostgreSQL", "content": "PostgreSQL is an open-source relational database management system. Data model: relational (tables, rows, columns) with strong SQL support. Scalability: vertical scaling, with extensions like Citus for horizontal. Consistency: ACID-compliant with strong consistency guarantees. Ideal use cases: complex queries, data warehousing, geospatial data, financial systems."},
        {"title": "MongoDB", "content": "MongoDB is a document-oriented NoSQL database. Data model: documents (JSON/BSON) in collections. Scalability: built-in horizontal scaling via sharding. Consistency: tunable (eventual to strong). Ideal use cases: content management, real-time analytics, IoT data, rapid prototyping."},
        {"title": "Cassandra", "content": "Apache Cassandra is a wide-column NoSQL database. Data model: partitioned row store. Scalability: excellent horizontal scaling with no single point of failure. Consistency: tunable (eventual consistency by default). Ideal use cases: time-series data, high write throughput, globally distributed applications."},

        # Energy & Environment
        {"title": "Renewable energy Germany", "content": "Germany's renewable energy share of electricity generation reached approximately 52% in 2023. Solar: ~12% (installed capacity ~82 GW). Wind: ~27% (onshore + offshore, capacity ~69 GW). Hydroelectric: ~3.5%. Germany aims for 80% renewable electricity by 2030."},
        {"title": "Renewable energy China", "content": "China is the world's largest renewable energy producer. Renewable share of electricity: ~32% in 2023. Solar: ~6% (capacity ~609 GW, world's largest). Wind: ~9% (capacity ~441 GW). Hydroelectric: ~15% (capacity ~421 GW, including Three Gorges Dam)."},
        {"title": "Renewable energy United States", "content": "US renewable energy share of electricity generation: ~22% in 2023. Solar: ~5% (capacity ~175 GW). Wind: ~10% (capacity ~148 GW). Hydroelectric: ~6% (capacity ~80 GW). The US aims for 100% clean electricity by 2035."},
        {"title": "Cryptocurrency mining energy", "content": "Bitcoin mining consumes approximately 150 TWh of electricity annually (2024 estimate), comparable to the energy consumption of a medium-sized country. Carbon footprint: estimated 65-90 million tonnes CO2 annually. Traditional banking system estimated at 260 TWh. Proposed solutions: renewable mining, proof-of-stake transition, carbon offsets."},

        # Healthcare
        {"title": "US healthcare system", "content": "The US healthcare system is primarily private insurance-based. Total spending: ~$4.5 trillion (2023), about 17.3% of GDP. Coverage: ~92% through private insurance, Medicare, Medicaid. Life expectancy: 77.5 years. Public satisfaction: mixed, with concerns about cost and access."},
        {"title": "UK healthcare system (NHS)", "content": "The UK National Health Service (NHS) is a publicly funded universal healthcare system. Total spending: ~£190 billion (2023), about 11% of GDP. Coverage: universal (100%). Life expectancy: 81.3 years. Public satisfaction: declining due to wait times, but strong support for the principle of free-at-point-of-use care."},
        {"title": "Japan healthcare system", "content": "Japan has a universal healthcare system with mandatory insurance. Total spending: ~$580 billion (2023), about 11% of GDP. Coverage: universal (100%). Life expectancy: 84.6 years (among highest globally). Public satisfaction: generally high, with good access and low costs."},

        # Quantum computing
        {"title": "Quantum computing overview", "content": "Key milestones: 1981 Feynman proposes quantum computing, 1994 Shor's algorithm, 2019 Google claims quantum supremacy with Sycamore (53 qubits). Current approaches: superconducting qubits (Google, IBM), trapped ions (IonQ, Quantinuum), photonic (Xanadu, PsiQuantum), topological (Microsoft). Major players: IBM (1000+ qubit processors), Google, Amazon Braket, Microsoft Azure Quantum. Practical applications: drug discovery, cryptography, optimization, materials science, financial modeling."},

        # Autonomous vehicles
        {"title": "Autonomous vehicles overview", "content": "SAE Levels: L0 (no automation) to L5 (full automation). Current state: most production vehicles at L2 (partial automation). Major companies: Waymo (L4 robotaxi in Phoenix/SF), Cruise (paused operations), Tesla (L2+ Autopilot/FSD), Zoox (Amazon), Aurora, Mobileye. Regulatory challenges: vary by state/country, liability questions, no federal US framework. Safety: Waymo reports lower crash rates than human drivers in operational domain."},

        # mRNA vaccines
        {"title": "mRNA vaccine technology", "content": "History: mRNA concept proposed 1990s by Katalin Karikó and Drew Weissman. Key breakthrough: modified nucleosides (2005) to reduce immune rejection. COVID-19: Pfizer-BioNTech and Moderna vaccines developed in under a year (2020), first approved December 2020. Over 13 billion doses administered globally. Future potential: cancer vaccines (personalized neoantigen), flu, HIV, malaria, autoimmune diseases."},

        # Remote work
        {"title": "Remote work analysis", "content": "Productivity: Stanford study shows 13% productivity increase for remote workers. WFH Research finds hybrid workers are equally productive. Employee wellbeing: reduced commute stress, better work-life balance, but risks of isolation and burnout. Environmental impact: reduced commuting emissions (average US commuter produces 4.6 tonnes CO2/year), but increased home energy use. Economic effects: reduced office real estate demand, redistribution of spending from urban to suburban/rural areas."},

        # Programming paradigms
        {"title": "Object-Oriented Programming (OOP)", "content": "Core principles: encapsulation, inheritance, polymorphism, abstraction. Strengths: models real-world entities well, code reuse through inheritance, large ecosystem of frameworks. Weaknesses: can lead to over-engineering, tight coupling, inheritance hierarchies can be fragile. Best for: large-scale applications, GUI frameworks, game development, enterprise software. Languages: Java, C++, Python, C#."},
        {"title": "Functional Programming", "content": "Core principles: immutability, pure functions, higher-order functions, referential transparency. Strengths: easier reasoning about code, naturally parallelizable, fewer bugs from side effects. Weaknesses: steeper learning curve, can be less intuitive for I/O-heavy tasks, performance overhead from immutability. Best for: data transformation pipelines, concurrent systems, mathematical computation, compiler design. Languages: Haskell, Clojure, Erlang, F#, Scala."},
        {"title": "Procedural Programming", "content": "Core principles: sequences of instructions, procedures/functions, top-down design, shared state. Strengths: simple and straightforward, efficient execution, easy to trace program flow. Weaknesses: difficulty managing complexity in large programs, shared state leads to bugs, poor code reuse. Best for: scripting, system programming, embedded systems, simple automation. Languages: C, Pascal, Bash, early BASIC."},

        # 2008 Financial Crisis
        {"title": "2008 Financial Crisis", "content": "Major contributing factors: (1) Subprime mortgage lending — banks issued mortgages to unqualified borrowers. (2) Securitization and CDOs — risky mortgages bundled into complex financial products. (3) Credit rating agency failures — AAA ratings given to high-risk securities. (4) Excessive leverage — banks operated with minimal capital reserves, ratios of 30:1 or higher. (5) Regulatory failures — Glass-Steagall repeal (1999), inadequate oversight of derivatives market. Effects: global recession, $2 trillion in bank losses, US unemployment peaked at 10%, housing prices dropped 30%, led to Dodd-Frank Act reforms."},
    ]

    facts_path = KNOWLEDGE_BASE_DIR / "facts.json"
    with open(facts_path, "w") as f:
        json.dump(facts, f, indent=2)
    print(f"  Created facts database: {facts_path} ({len(facts)} entries)")


def _create_web_cache():
    """Create the web cache for the web_lookup tool."""
    cache = {
        "renewable energy Germany": "Germany's Energiewende (energy transition) has pushed renewable electricity to ~52% of generation in 2023. Solar PV capacity reached 82 GW, making Germany Europe's largest solar market. Onshore wind provides the bulk of renewable generation at ~27%. The country plans to phase out coal by 2038 and achieve 80% renewable electricity by 2030. Key challenges: grid expansion, storage, and intermittency management.",

        "renewable energy China": "China dominates global renewable energy deployment. In 2023, China added more solar capacity (217 GW) than the rest of the world combined. Total solar capacity exceeds 609 GW. Wind capacity reached 441 GW. The Three Gorges Dam remains the world's largest hydroelectric facility at 22.5 GW. Despite these achievements, coal still provides ~60% of China's electricity due to massive overall demand growth.",

        "renewable energy United States": "US renewable electricity generation reached ~22% in 2023. Texas leads in wind capacity, California in solar. The Inflation Reduction Act (2022) provides $369 billion in clean energy incentives. Utility-scale solar is now the cheapest form of new electricity generation in most of the US. Challenges: permitting delays, grid interconnection queues, and political uncertainty around clean energy subsidies.",

        "quantum computing": "Quantum computing uses quantum mechanical phenomena (superposition, entanglement) to process information. IBM's Condor processor (2023) has 1,121 superconducting qubits. Google's Sycamore demonstrated quantum supremacy in 2019. Current NISQ (Noisy Intermediate-Scale Quantum) devices have 50-1000+ qubits but high error rates. Error correction remains the key challenge. Estimated timeline to fault-tolerant quantum computing: 2030-2040.",

        "cryptocurrency mining environmental impact": "Bitcoin's proof-of-work consensus mechanism requires enormous computational power. Annual energy: ~150 TWh (2024), rivaling countries like Poland. About 40-60% uses renewable energy (varies by estimate). Ethereum transitioned to proof-of-stake in 2022, reducing energy use by ~99.95%. Solutions: renewable-powered mining, waste heat utilization, carbon credits, regulatory requirements for renewable sourcing.",

        "autonomous vehicles": "Self-driving technology uses lidar, radar, cameras, and AI. Waymo operates commercial robotaxi service in Phoenix and San Francisco (L4). Tesla's Full Self-Driving (FSD) operates at L2+ requiring driver supervision. Key challenges: edge cases (unusual road situations), weather conditions, regulatory patchwork, liability framework. NHTSA investigating multiple incidents. China's Baidu Apollo also offers commercial L4 service in select cities.",

        "mRNA vaccine technology": "mRNA vaccines deliver genetic instructions for cells to produce a target protein, triggering immune response. Breakthrough: Katalin Karikó and Drew Weissman's modified nucleoside technology (2005) solved inflammatory response problem. COVID-19 vaccines (Pfizer-BioNTech, Moderna) demonstrated ~95% efficacy. Manufacturing advantage: can be produced faster than traditional vaccines. Pipeline: personalized cancer vaccines (Moderna/Merck mRNA-4157 in Phase 3), flu, RSV, HIV, Zika.",

        "remote work productivity": "Meta-analysis of 22 studies shows remote workers are 5-13% more productive for individual tasks but may face challenges in collaborative work. Stanford professor Nick Bloom's research: hybrid work (3 days office, 2 days home) shows no productivity loss and reduces attrition by 33%. Downsides: reduced spontaneous innovation, weaker social bonds, difficulty onboarding new employees, timezone coordination costs.",

        "2008 financial crisis": "The 2008 crisis was triggered by the collapse of the US housing bubble. Subprime mortgages were packaged into mortgage-backed securities (MBS) and collateralized debt obligations (CDOs). When housing prices fell, these securities became toxic. Lehman Brothers collapsed September 2008. The crisis spread globally through interconnected financial markets. Response: $700B TARP bailout, Fed dropped rates to near zero, quantitative easing programs. Long-term effects: Dodd-Frank regulation, bank stress testing, lasting distrust of financial institutions.",

        "healthcare system comparison": "US: highest spending ($12,500/capita), private insurance-based, lower life expectancy (77.5y). UK: NHS publicly funded ($5,600/capita), universal coverage, higher life expectancy (81.3y), but wait time challenges. Japan: mandatory insurance ($4,800/capita), universal coverage, highest life expectancy (84.6y), excellent access but aging population strains system. Key differentiator: single-payer systems (UK, Japan) achieve better outcomes at lower per-capita cost than the US market-based model.",

        "PostgreSQL vs MongoDB vs Cassandra": "PostgreSQL: best for complex queries, ACID compliance, strong consistency. Full SQL support, JSONB for semi-structured data, excellent for analytics. MongoDB: best for flexible schemas, rapid development, content management. Document model maps well to application objects. Built-in horizontal scaling. Cassandra: best for write-heavy workloads, time-series data, global distribution. Linear scalability, no single point of failure. Trade-off: limited query flexibility, eventual consistency by default.",

        "OOP vs functional vs procedural programming": "OOP organizes code around objects with state and behavior — dominant in enterprise software (Java, C#). Functional programming treats computation as mathematical function evaluation — gaining popularity for concurrent/parallel systems (Haskell, Scala, Rust's functional features). Procedural programming uses sequential instructions and procedures — still dominant in systems programming (C) and scripting. Modern languages (Python, Kotlin, Rust) blend all three paradigms.",

        "nuclear energy pros and cons": "Pros: low carbon emissions (12 gCO2/kWh lifecycle), reliable baseload power, high energy density, small land footprint. Cons: high upfront cost ($6-12 billion per reactor), nuclear waste storage (radioactive for thousands of years), accident risk (Chernobyl, Fukushima), long construction times (10-15 years), weapons proliferation concerns. New developments: small modular reactors (SMRs) promise lower cost and faster deployment. Countries expanding: China, India, UAE. Countries phasing out: Germany (completed 2023).",
    }

    cache_path = KNOWLEDGE_BASE_DIR / "web_cache.json"
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)
    print(f"  Created web cache: {cache_path} ({len(cache)} entries)")


if __name__ == "__main__":
    create_knowledge_base()
