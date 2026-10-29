# National school exam digitization rollout

## Nationwide digital final examinations

A country wants to replace paper-based final secondary-school exams with a digital exam system.

The reform sounds simple:

> “Students will take national exams on computers instead of paper.”

But beneath that sentence sits a federated transformation problem.

## 2. Actors

* `a1`: national education ministry
* `a2`: exam authority
* `a3`: regional education boards
* `a4`: school administrators
* `a5`: teachers / invigilators
* `a6`: students
* `a7`: disability accommodation office
* `a8`: device and platform vendor
* `a9`: telecom / network providers
* `a10`: courts / legal oversight body
* `a11`: cybersecurity authority

## 3. Objectives

* `o1`: exam integrity
* `o2`: equal fairness across schools and regions
* `o3`: operational continuity on exam day
* `o4`: grading efficiency
* `o5`: accessibility for students with disabilities
* `o6`: public trust and legitimacy
* `o7`: lower long-term administrative cost
* `o8`: resilience against cheating and cyberattack

## 4. Capabilities

* `k1`: traditional paper exam delivery
* `k2`: digital exam authoring platform
* `k3`: secure student login and identity verification
* `k4`: locked-down exam-taking application
* `k5`: local offline exam caching
* `k6`: real-time submission to central servers
* `k7`: auto-marking for structured questions
* `k8`: digital accommodations interface
* `k9`: remote audit and proctoring dashboard
* `k10`: post-failure recovery and re-sync process
* `k11`: emergency paper fallback kit
* `k12`: plagiarism / anomaly detection
* `k13`: school device readiness management
* `k14`: region-wide scheduling coordination

## 5. Dependencies

* `d1`: every school has sufficient functioning devices
* `d2`: electricity reliability for exam sessions
* `d3`: internet connectivity or offline sync readiness
* `d4`: student identity records are accurate
* `d5`: invigilators are trained
* `d6`: legal approval of digital exam results
* `d7`: accessibility workflows tested
* `d8`: cybersecurity certification complete
* `d9`: data protection approval granted
* `d10`: item bank successfully migrated
* `d11`: telecom surge capacity confirmed
* `d12`: paper fallback logistics preserved
* `d13`: dispute-resolution process updated for digital evidence
* `d14`: interoperability between ministry, vendor, and regional systems works

## 6. Constraints

* `q1`: national law requires equal treatment across all exam candidates
* `q2`: no student may be disadvantaged by disability, region, or school wealth
* `q3`: high-stakes exams must be legally challengeable and auditable
* `q4`: exam content must remain confidential before the sitting
* `q5`: the exam must proceed even under partial technical failure
* `q6`: budget caps prohibit replacing all school hardware at once
* `q7`: unions limit invigilator workflow changes without training
* `q8`: privacy law restricts biometric proctoring
* `q9`: some regions prohibit external cloud hosting of student data
* `q10`: schools cannot suspend all legacy processes immediately
* `q11`: national results calendar cannot slip beyond a fixed deadline

## 7. Boundaries

* `β1`: national ministry ↔ regional boards
* `β2`: school operations ↔ national exam platform
* `β3`: vendor system ↔ government records
* `β4`: urban schools ↔ rural schools
* `β5`: accessibility office ↔ standard exam workflow
* `β6`: privacy law ↔ proctoring technology
* `β7`: legal oversight ↔ operational design
* `β8`: online infrastructure ↔ offline continuity mechanisms

## 8. States

* `s0`: fully paper-based national exam system
* `s1`: digital authoring, paper sitting
* `s2`: limited pilot digital exams in selected schools
* `s3`: mixed-mode national operation, some digital and some paper
* `s4`: digital exams with offline local resilience
* `s5`: fully digital centralized real-time exam operation
* `s6`: digitally integrated target state with audited fallback capacity
* `s7`: degraded emergency state using paper fallback during system failure
* `s8`: legally contested state after exam irregularity
* `s9`: regionally asymmetric state where some regions are compliant and others are not

## 9. Transitions

* `τ1`: move from paper-only to digital authoring but paper sitting
* `τ2`: expand pilot digital exams to selected schools
* `τ3`: move from pilot to mixed-mode nationwide digital-paper coexistence
* `τ4`: move directly from paper-only to full digital delivery
* `τ5`: add offline caching and local continuity capability
* `τ6`: introduce digital accommodations layer
* `τ7`: retire paper fallback
* `τ8`: centralize all live submissions in real time
* `τ9`: revert from digital exam session to emergency paper fallback
* `τ10`: split rollout by region according to readiness
* `τ11`: delay deployment and preserve paper while dependencies are repaired
* `τ12`: enable anomaly detection and digital audit trail
* `τ13`: legal remediation transition after contested results
