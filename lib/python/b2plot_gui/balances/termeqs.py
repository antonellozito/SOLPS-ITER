"""Equations of the terms of the balances (see equations.py), simplified
from the model equations of B2.5 and the code: keys (quantity, role,
field, name or None), role "flux" (the poloidal component of a face
flux, parallel terms projected with b_theta = B_theta/B), "radial" (its
radial component) or "source"; quantity "heat" for the heat terms of all
energy balances. Values: the equation and its meaning, text lines of
words and $mathtext$."""

EQ = {
    # particles, poloidal fluxes
    ('particles', 'flux', 'fna_pll', None):
        r"$\Gamma^{\parallel}_{a,\theta} = n_a\,b_\theta\,u_{\parallel"
        r" a}$" "\n"
        r"parallel flow projected on the poloidal direction ($b_\theta ="
        r" B_\theta/B$)",
    ('particles', 'flux', 'fna_ecrb', None):
        r"$\Gamma^{E}_{a,\theta} ="
        r" -n_a\,\frac{B_\varphi}{B^2}\,\nabla_r\Phi$" "\n"
        r"$E\times B$ drift of the charged species ($B_\varphi$: toroidal"
        r" field)",
    ('particles', 'flux', 'fna_dia', None):
        r"$\Gamma^{\mathrm{dia}}_{a,\theta} = \frac{n_a T_i"
        r" B_\varphi}{Z_a e}\,\nabla_r\left(\frac{1}{B^2}\right)$" "\n"
        r"diamagnetic drift flux without its divergence-free part",
    ('particles', 'flux', 'fna_nanom', None):
        r"$\Gamma^{D_n}_{a,\theta} = -D_{n,a}\,\nabla_\theta n_a$" "\n"
        r"anomalous diffusion driven by the density gradient",
    ('particles', 'flux', 'fna_panom', None):
        r"$\Gamma^{D_p}_{a,\theta} = -D_{p,a}\,\nabla_\theta p_a$" "\n"
        r"with $p_a = n_a(Z_a T_e + T_i)$",
    ('particles', 'flux', 'fna_pinch', None):
        r"$\Gamma^{\mathrm{pinch}}_{a,\theta} ="
        r" n_a\,V^{\mathrm{AN}}_{a,\theta}$" "\n"
        r"with $V^{\mathrm{AN}}_a$ the anomalous pinch velocity",
    ('particles', 'flux', 'fna_ch', None):
        r"$\Gamma^{j}_{a,\theta} = \frac{1}{Z_a e}\sum_k"
        r" j^{(k)}_{a,\theta}$" "\n"
        r"ion parts of the anomalous, inertia, viscosity and"
        r" Reynolds-stress" "\n"
        r"currents $j^{(k)}_a$, carried by species $a$",
    ('particles', 'flux', 'fna_pschused', None):
        r"$\Gamma^{\mathrm{PS}}_{a,\theta} = -\frac{B_\varphi}{Z_a"
        r" e}\left(\frac{1}{B^2} - \frac{1}{\langle"
        r" B^2\rangle}\right)\nabla_r(n_a T_i)$" "\n"
        r"Pfirsch-Schlüter flux (in place of the diamagnetic flux);" "\n"
        r"$\langle B^2\rangle$: average of $B^2$ over the core",
    # particles, radial fluxes
    ('particles', 'radial', 'fna_pll', None):
        r"$\Gamma^{\parallel}_{a,r} = 0$" "\n"
        r"the parallel flow has no radial component",
    ('particles', 'radial', 'fna_ecrb', None):
        r"$\Gamma^{E}_{a,r} = n_a\,\frac{B_\varphi}{B^2}\,\nabla_\theta\P"
        r"hi$" "\n"
        r"$E\times B$ drift of the charged species ($B_\varphi$: toroidal"
        r" field)",
    ('particles', 'radial', 'fna_dia', None):
        r"$\Gamma^{\mathrm{dia}}_{a,r} = -\frac{n_a T_i B_\varphi}{Z_a"
        r" e}\,\nabla_\theta\left(\frac{1}{B^2}\right)$" "\n"
        r"diamagnetic drift flux without its divergence-free part",
    ('particles', 'radial', 'fna_nanom', None):
        r"$\Gamma^{D_n}_{a,r} = -D_{n,a}\,\nabla_r n_a$" "\n"
        r"anomalous diffusion driven by the density gradient",
    ('particles', 'radial', 'fna_panom', None):
        r"$\Gamma^{D_p}_{a,r} = -D_{p,a}\,\nabla_r p_a$" "\n"
        r"with $p_a = n_a(Z_a T_e + T_i)$",
    ('particles', 'radial', 'fna_pinch', None):
        r"$\Gamma^{\mathrm{pinch}}_{a,r} = n_a\,V^{\mathrm{AN}}_{a,r}$" "\n"
        r"with $V^{\mathrm{AN}}_a$ the anomalous pinch velocity",
    ('particles', 'radial', 'fna_ch', None):
        r"$\Gamma^{j}_{a,r} = \frac{1}{Z_a e}\sum_k j^{(k)}_{a,r}$" "\n"
        r"ion parts of the anomalous, inertia, viscosity and"
        r" Reynolds-stress" "\n"
        r"currents $j^{(k)}_a$, carried by species $a$",
    ('particles', 'radial', 'fna_pschused', None):
        r"$\Gamma^{\mathrm{PS}}_{a,r} = \frac{B_\varphi}{Z_a"
        r" e}\left(\frac{1}{B^2} - \frac{1}{\langle"
        r" B^2\rangle}\right)\nabla_\theta(n_a T_i)$" "\n"
        r"Pfirsch-Schlüter flux (in place of the diamagnetic flux);" "\n"
        r"$\langle B^2\rangle$: average of $B^2$ over the core",
    # particles, sources
    ('particles', 'source', 'b2stel_sna_ion_bal',
     'Ionisation from the lower charge state'):
        r"$S_a = \langle\sigma v\rangle_{\mathrm{ion},a-1}\,n_e\,n_{a-1}$" "\n"
        r"gain by ionisation of the next lower charge state $a-1$",
    ('particles', 'source', 'b2stel_sna_ion_bal',
     'Ionisation to the higher charge state'):
        r"$S_a = -\langle\sigma v\rangle_{\mathrm{ion},a}\,n_e\,n_a$" "\n"
        r"loss by ionisation of species $a$ to the charge state $a+1$",
    ('particles', 'source', 'b2stel_sna_rec_bal',
     'Recombination to the lower charge state'):
        r"$S_a = -\langle\sigma v\rangle_{\mathrm{rec},a}\,n_e\,n_a$" "\n"
        r"loss by recombination of species $a$ to the charge state $a-1$",
    ('particles', 'source', 'b2stel_sna_rec_bal',
     'Recombination from the higher charge state'):
        r"$S_a = \langle\sigma v\rangle_{\mathrm{rec},a+1}\,n_e\,n_{a+1}$" "\n"
        r"gain by recombination of the next higher charge state $a+1$",
    ('particles', 'source', 'b2stcx_sna_bal', None):
        r"$S_a^{\mathrm{cx}} = \langle\sigma"
        r" v\rangle_{\mathrm{cx},a+1}\,n_0\,n_{a+1} - \langle\sigma"
        r" v\rangle_{\mathrm{cx},a}\,n_0\,n_a$" "\n"
        r"charge exchange of the ions with the hydrogen atoms (density"
        r" $n_0$):" "\n"
        r"$\mathrm{H}^0 + A^{z+} \rightarrow \mathrm{H}^+ + A^{(z-1)+}$",
    ('particles', 'source', 'b2stbm_sna_bal', None):
        r"$S_a^{\mathrm{bm}} = S_{a,0} + S_{a,1}\,n_a$" "\n"
        r"application-specific source from an external code",
    ('particles', 'source', 'ext_sna_bal', None):
        r"$S_a^{\mathrm{ext}} = f_a(r)\,g_a(s_\parallel)$" "\n"
        r"prescribed source: radial and parallel profiles from the source"
        r" input",
    # potential, poloidal fluxes
    ('potential', 'flux', 'fch_p', None):
        r"$j^{\parallel}_{\theta} ="
        r" \sigma_\parallel\left(\frac{\nabla_\theta p_e}{e n_e} -"
        r" \nabla_\theta\Phi\right) - \alpha_e\,\nabla_\theta T_e$" "\n"
        r"Ohm's law along B; $\sigma_\parallel$: conductivity, $\alpha_e$:"
        r" thermoelectric coefficient",
    ('potential', 'flux', 'fch_in', None):
        r"$j^{\mathrm{in}}_{\theta} ="
        r" \sigma_{\mathrm{in}}\left[-b_\varphi^2\left(\nabla_\theta\Phi"
        r" + \frac{\nabla_\theta(n_i T_i)}{e n_i}\right) + B_\varphi"
        r" V_{0,r}\right]$" "\n"
        r"ion-neutral friction current, $\sigma_{\mathrm{in}} = \mu\,n_i"
        r" n_0\langle\sigma v\rangle_{\mathrm{cx}}/B^2$" "\n"
        r"$\mu$: reduced mass, $V_0$: atom velocity",
    ('potential', 'flux', 'fch_dia', None):
        r"$j^{\mathrm{dia}}_{\theta} ="
        r" p\,B_\varphi\,\nabla_r\left(\frac{1}{B^2}\right)$" "\n"
        r"with $p = p_e + p_i$; diamagnetic current without its"
        r" divergence-free part",
    ('potential', 'flux', 'fch_vispar', None):
        r"$j^{\mathrm{vis}\parallel}_{\theta} ="
        r" -\frac{B_\varphi\sqrt{B}}{3B_\theta}\,\eta_\parallel\,\nabla_r"
        r"\left(\frac{1}{B^2}\right)\nabla_\theta\left(\sqrt{B}\,u_{\para"
        r"llel i}\right)$" "\n"
        r"parallel ion viscosity current; $\eta_\parallel$: classical"
        r" viscosity",
    ('potential', 'flux', 'fch_visper', None):
        r"$j^{\mathrm{vis}\perp}_{\theta} = 0$" "\n"
        r"the perpendicular viscosity current is radial only",
    ('potential', 'flux', 'fch_visq', None):
        r"$j^{\mathrm{visq}}_{\theta} ="
        r" -0.24\,\alpha\,\tau_i\,\frac{B_\varphi"
        r" B_\theta}{B^{3/2}}\,\nabla_r\left(\frac{1}{B^2}\right)\nabla_"
        r"\theta\left(\sqrt{B}\,q_{\parallel i}\right)$" "\n"
        r"heat-flux part of the parallel ion viscosity (closed surfaces"
        r" only);" "\n"
        r"$q_{\parallel i}$: parallel ion heat flux, $\alpha$: neoclassical"
        r" coefficient",
    ('potential', 'flux', 'fch_inert', None):
        r"$j^{\mathrm{inert}}_{\theta} ="
        r" B_\varphi\,\nabla_r\left(\frac{1}{B^2}\right)\sum_a\frac{m_a"
        r" n_a u_{\parallel a}^2}{2}$" "\n"
        r"inertia (centrifugal drift) current of the parallel ion flow",
    ('potential', 'flux', 'fch_anml', None):
        r"$j^{\mathrm{AN}}_{\theta} ="
        r" -\sigma^{\mathrm{AN}}\,\nabla_\theta\Phi$" "\n"
        r"anomalous current; $\sigma^{\mathrm{AN}}$: anomalous conductivity",
    ('potential', 'flux', 'fch_viskt', None):
        r"$j^{\mathrm{RS}}_{\theta} ="
        r" -\frac{B_\varphi}{B^2}\,\nabla_r\left(\frac{2}{3}n_i\kappa\rig"
        r"ht)$" "\n"
        r"Reynolds-stress current of the turbulence model" "\n"
        r"($\kappa$: turbulent kinetic energy per particle)",
    # potential, radial fluxes
    ('potential', 'radial', 'fch_p', None):
        r"$j^{\parallel}_{r} = 0$" "\n"
        r"the parallel current has no radial component",
    ('potential', 'radial', 'fch_in', None):
        r"$j^{\mathrm{in}}_{r} = -\sigma_{\mathrm{in}}\left(\nabla_r\Phi"
        r" + \frac{\nabla_r(n_i T_i)}{e n_i} + B\,V_{0,\perp}\right)$" "\n"
        r"ion-neutral friction current, $\sigma_{\mathrm{in}} = \mu\,n_i"
        r" n_0\langle\sigma v\rangle_{\mathrm{cx}}/B^2$" "\n"
        r"$\mu$: reduced mass, $V_0$: atom velocity",
    ('potential', 'radial', 'fch_dia', None):
        r"$j^{\mathrm{dia}}_{r} ="
        r" -p\,B_\varphi\,\nabla_\theta\left(\frac{1}{B^2}\right)$" "\n"
        r"with $p = p_e + p_i$; diamagnetic current without its"
        r" divergence-free part",
    ('potential', 'radial', 'fch_vispar', None):
        r"$j^{\mathrm{vis}\parallel}_{r} ="
        r" \frac{B_\varphi\sqrt{B}}{3B_\theta}\,\eta_\parallel\,\nabla_\t"
        r"heta\left(\frac{1}{B^2}\right)\nabla_\theta\left(\sqrt{B}\,u_{"
        r"\parallel i}\right)$" "\n"
        r"parallel ion viscosity current; $\eta_\parallel$: classical"
        r" viscosity",
    ('potential', 'radial', 'fch_visper', None):
        r"$j^{\mathrm{vis}\perp}_{r} ="
        r" -\frac{1}{B}\,\nabla_r\left(\frac{\eta^{\mathrm{AN}}_a}{4}\,\n"
        r"abla_r V_{a\perp}\right)$" "\n"
        r"$V_{a\perp} = -\frac{1}{B}\left(\nabla_r\Phi + \frac{\nabla_r(n_a"
        r" T_i)}{Z_a e n_a}\right)$, $\eta^{\mathrm{AN}}_a$: anomalous"
        r" viscosity",
    ('potential', 'radial', 'fch_visq', None):
        r"$j^{\mathrm{visq}}_{r} = 0.24\,\alpha\,\tau_i\,\frac{B_\varphi"
        r" B_\theta}{B^{3/2}}\,\nabla_\theta\left(\frac{1}{B^2}\right)\na"
        r"bla_\theta\left(\sqrt{B}\,q_{\parallel i}\right)$" "\n"
        r"heat-flux part of the parallel ion viscosity (closed surfaces"
        r" only);" "\n"
        r"$q_{\parallel i}$: parallel ion heat flux, $\alpha$: neoclassical"
        r" coefficient",
    ('potential', 'radial', 'fch_inert', None):
        r"$j^{\mathrm{inert}}_{r} ="
        r" -B_\varphi\,\nabla_\theta\left(\frac{1}{B^2}\right)\sum_a\frac"
        r"{m_a n_a u_{\parallel a}^2}{2}$" "\n"
        r"inertia (centrifugal drift) current of the parallel ion flow",
    ('potential', 'radial', 'fch_anml', None):
        r"$j^{\mathrm{AN}}_{r} = -\sigma^{\mathrm{AN}}\,\nabla_r\Phi$" "\n"
        r"anomalous current; $\sigma^{\mathrm{AN}}$: anomalous conductivity",
    ('potential', 'radial', 'fch_viskt', None):
        r"$j^{\mathrm{RS}}_{r} ="
        r" \frac{B_\varphi}{B^2}\,\nabla_\theta\left(\frac{2}{3}n_i\kappa"
        r"\right) - \frac{1}{B}\,\nabla_r\left(\eta_E\,\nabla_r"
        r" V_E\right)$" "\n"
        r"$\kappa$: turbulent kinetic energy, $V_E = \nabla_r\Phi/B$:"
        r" binormal $E\times B$ velocity," "\n"
        r"$\eta_E \propto m_i n_i D_E$: turbulent viscosity of the $E\times"
        r" B$ flow",
    # potential, sources
    ('potential', 'source', 'b2stbm_sch_bal', None):
        r"$S^{\mathrm{bm}}_{\mathrm{ch}} = S_{\mathrm{ch},0} +"
        r" S_{\mathrm{ch},1}\,\Phi$" "\n"
        r"application-specific charge source from an external code",
    ('potential', 'source', 'ext_sch_bal', None):
        r"$S^{\mathrm{ext}}_{\mathrm{ch}} = f(r)\,g(s_\parallel)$" "\n"
        r"prescribed charge source: radial and parallel profiles from the"
        r" input",
    # momentum, poloidal fluxes
    ('momentum', 'flux', 'fmo_flua', None):
        r"$\Pi_{a,\theta} = m_a u_{\parallel a}\,\Gamma_{a,\theta}"
        r" \approx m_a n_a u_{\parallel a}^2\,b_\theta$" "\n"
        r"$\Gamma_{a,\theta}$: poloidal particle flux (parallel flow with"
        r" $b_\theta$, drifts)",
    ('momentum', 'flux', 'fmo_cvsa', None):
        r"$\Pi^{vis}_{a,\theta} = -\eta_{a,\theta}\nabla_\theta"
        r" u_{\parallel a}$, $\eta_{a,\theta} = \eta^{AN}_a +"
        r" \frac{4}{3}\eta^{CL}_{\parallel a}b_\theta^2$" "\n"
        r"$\eta^{CL}_{\parallel a}$: classical parallel viscosity,"
        r" $\eta^{AN}_a$: anomalous viscosity",
    ('momentum', 'flux', 'fmo_hybr', None):
        r"$\Pi^{hyb}_{a,\theta} = \eta_{a,\theta}\left(1 + \frac{|P|}{2}"
        r" - \sqrt{1 + \frac{P^2}{4}}\right)\nabla_\theta u_{\parallel"
        r" a}$" "\n"
        r"numerical correction of the upwind scheme, cell Péclet number $P ="
        r" m_a\Gamma_{a,\theta}\Delta l/\eta_{a,\theta}$",
    # momentum, radial fluxes
    ('momentum', 'radial', 'fmo_flua', None):
        r"$\Pi_{a,r} = m_a u_{\parallel a}\,\Gamma_{a,r}$" "\n"
        r"$\Gamma_{a,r}$: radial particle flux (anomalous diffusion and"
        r" pinch," "\n"
        r"drifts, currents) carrying the parallel momentum",
    ('momentum', 'radial', 'fmo_cvsa', None):
        r"$\Pi^{vis}_{a,r} = -\eta^{AN}_a\nabla_r u_{\parallel a}$" "\n"
        r"radial transport of parallel momentum by the anomalous"
        r" viscosity" "\n"
        r"$\eta^{AN}_a = m_a n_a\nu^{vis}_a$",
    ('momentum', 'radial', 'fmo_hybr', None):
        r"$\Pi^{hyb}_{a,r} = \eta^{AN}_a\left(1 + \frac{|P|}{2} -"
        r" \sqrt{1 + \frac{P^2}{4}}\right)\nabla_r u_{\parallel a}$" "\n"
        r"numerical correction of the upwind scheme, cell Péclet number $P ="
        r" m_a\Gamma_{a,r}\Delta l/\eta^{AN}_a$",
    # momentum, sources
    ('momentum', 'source', 'b2stel_smq_ion_bal', None):
        r"$S_I = m_a n_e\left(\langle\sigma"
        r" v\rangle^{ion}_{a-1}n_{a-1}u_{\parallel a-1} - \langle\sigma"
        r" v\rangle^{ion}_{a}n_a u_{\parallel a}\right)$" "\n"
        r"momentum of the lower charge state ionised into $a$, minus the" "\n"
        r"momentum lost by the ionisation of $a$ (B2.5 species)",
    ('momentum', 'source', 'b2stel_smq_rec_bal', None):
        r"$S_R = m_a n_e\left(\langle\sigma"
        r" v\rangle^{rec}_{a+1}n_{a+1}u_{\parallel a+1} - \langle\sigma"
        r" v\rangle^{rec}_{a}n_a u_{\parallel a}\right)$" "\n"
        r"momentum of the higher charge state recombining into $a$,"
        r" minus the" "\n"
        r"momentum lost by the recombination of $a$ (B2.5 species)",
    ('momentum', 'source', 'b2stcx_smq_bal', None):
        r"$S_{CX} = m_i n_0 n_i\langle\sigma v\rangle_{cx}(u_{\parallel"
        r" 0} - u_{\parallel i})$ for the main ions" "\n"
        r"charge exchange with the B2.5 fluid neutrals: the ion loses"
        r" its momentum," "\n"
        r"the new ion gets the momentum of the neutral",
    ('momentum', 'source', 'b2sifr_smoch_bal', None):
        r"$S_{fr,i} = \sum_{b\neq"
        r" a}\frac{\sqrt{m_p\mu_{ab}}}{\zeta_p}Z_a^2 Z_b^2 n_a"
        r" n_b\,(u_{\parallel b} - u_{\parallel a})$" "\n"
        r"friction with the other ions, $\mu_{ab} = m_a m_b/(m_a + m_b)$," "\n"
        r"$\zeta_p \propto T_i^{3/2}/\ln\Lambda$: collision time constant",
    ('momentum', 'source', 'b2sifr_smotf_ehxp_bal', None):
        r"$S_{\hat E} = Z_a n_a\left(1 - \frac{Z_a"
        r" n_e}{n_{e2}}\right)e\hat E_\parallel$, $n_{e2} = \sum_b Z_b^2"
        r" n_b$" "\n"
        r"$e n_e\hat E_\parallel = \nabla_\parallel p_e - e"
        r" n_e\nabla_\parallel\Phi$" "\n"
        r"force of the effective parallel electric field on the ions",
    ('momentum', 'source', 'b2sifr_smotf_cthe_bal', None):
        r"$S_{th,e} = Z_a n_a\left(\frac{Z_a n_e}{n_{e2}} -"
        r" 1\right)c_{th,e}\nabla_\parallel T_e$, $n_{e2} = \sum_b Z_b^2"
        r" n_b$" "\n"
        r"electron thermal force",
    ('momentum', 'source', 'b2sifr_smotf_cthi_bal', None):
        r"$S_{th,i} = Z_a n_a\left(\frac{Z_a n_e}{n_{e2}} -"
        r" 1\right)c_{th,i}\nabla_\parallel T_i$, $n_{e2} = \sum_b Z_b^2"
        r" n_b$" "\n"
        r"ion thermal force",
    ('momentum', 'source', 'b2sifr_smofrea_bal', None):
        r"$S_{fr,e} = \frac{e^2 Z_a^2}{\sigma_\parallel Z_{eff}}\,n_e"
        r" n_a\,(u_{\parallel e} - u_{\parallel a})$" "\n"
        r"electron-ion friction; $\sigma_\parallel$: parallel electrical"
        r" conductivity," "\n"
        r"$u_{\parallel e}$: electron velocity (from the parallel current)",
    ('momentum', 'source', 'b2sifr_smofria_bal', None):
        r"$S_{fr,i} = \sum_{b\neq"
        r" a}\frac{\sqrt{m_p\mu_{ab}}}{\zeta_p}Z_a^2 Z_b^2 n_a n_b"
        r" K_{ab}(u_{\parallel b} - u_{\parallel a})$" "\n"
        r"ion-ion friction, $\mu_{ab} = \frac{m_a m_b}{m_a + m_b}$" "\n"
        r"$K_{ab}$: correction coefficient, $\zeta_p \propto"
        r" T_i^{3/2}/\ln\Lambda$: collision time constant",
    ('momentum', 'source', 'b2sifr_smotfea_bal', None):
        r"$S_{th,e} = \tilde c^{(2)}_e\,Z_a^2 n_a\,\nabla_\parallel T_e$" "\n"
        r"electron thermal force; $\tilde c^{(2)}_e \approx 0.73$ for"
        r" $Z_{eff} = 1$",
    ('momentum', 'source', 'b2sifr_smotfia_bal', None):
        r"$S_{th,i} = \sum_{b\neq a}Z_a^2 Z_b^2\sqrt{\mu_{ab}}\,n_a"
        r" n_b\left(\frac{K_{ab}}{\kappa_b} -"
        r" \frac{K_{ba}}{\kappa_a}\right)\nabla_\parallel T_i$" "\n"
        r"ion thermal force, $\kappa_a = \sum_r Z_a^2 Z_r^2"
        r" n_r\sqrt{\mu_{ar}}$, $\mu_{ab} = \frac{m_a m_b}{m_a + m_b}$" "\n"
        r"$K_{ab}$: thermal force coefficients",
    ('momentum', 'source', 'b2siav_smovh_bal', None):
        r"$S_{vh} = B^{3/2}\nabla_\parallel\left(\frac{\alpha^{NEO}\tilde"
        r"\tau_a}{B^2}\nabla_\parallel\left(B^{1/2}\tilde q_{\parallel"
        r" a}\right)\right)$" "\n"
        r"heat-flux part of the neoclassical parallel viscosity of the"
        r" main ions" "\n"
        r"on the closed surfaces; $\tilde q_{\parallel a}$: parallel ion"
        r" heat flux",
    ('momentum', 'source', 'b2siav_smovv_bal', None):
        r"$S_{vv} = B^{1/2}u_{\parallel"
        r" a}\,\nabla_\theta\cdot\left(\frac{4}{3}\eta^{CL}_{a,\theta}B^{"
        r"-1/2}\nabla_\theta\ln\left(R\,B^{1/2}\right)\right)$" "\n"
        r"residual part of the classical parallel viscosity of the main"
        r" ions" "\n"
        r"from the variation of $B$ and $R$, $\eta^{CL}_{a,\theta} ="
        r" \eta^{CL}_{\parallel a}b_\theta^2$",
    ('momentum', 'source', 'b2siav_smovi_bal', None):
        r"$S_{vi} = \frac{4}{3}B^{3/2}\nabla_\parallel\left(\frac{\eta^{C"
        r"L}_{\parallel a}}{\rho^{rel}_a"
        r" B^2}\nabla_\parallel\left(B^{1/2}\sum_{b\neq a}\rho^{rel}_b"
        r" u_{\parallel b}\right)\right)$" "\n"
        r"cross-ion viscous stress (Zhdanov closure), driven by the flow"
        r" of the" "\n"
        r"other ions; $\rho^{rel}_b = m_b n_b/\sum_c m_c n_c$",
    ('momentum', 'source', 'b2sicf_smo_bal', None):
        r"$S_{CF} = m_a n_a u_{\parallel a}^2\,\nabla_\parallel\ln R$" "\n"
        r"centrifugal force of the parallel flow ($R$: major radius)",
    ('momentum', 'source', 'b2sian_smo_bal', None):
        r"$S_{AN} = -j^{AN}_{a,r}\,\frac{B\,B_\theta}{B_\varphi}$" "\n"
        r"toroidal $j\times B$ force of the radial anomalous current"
        r" $j^{AN}_{a,r}$" "\n"
        r"of the ions, as parallel momentum ($B_\varphi$: toroidal field)",
    ('momentum', 'source', 'b2sigp_smogpi_bal', None):
        r"$S_{\nabla p_i} = -\nabla_\parallel(n_a T_i)$" "\n"
        r"ion static pressure gradient",
    ('momentum', 'source', 'b2sigp_smogpe_bal', None):
        r"b2sigp_style 1: $-\frac{Z_a n_a}{n_e}\nabla_\parallel p_e$,"
        r" electron pressure gradient" "\n"
        r"b2sigp_style 2: $-Z_a e n_a\nabla_\parallel\Phi$, electric"
        r" field (potential gradient)" "\n"
        r"with $p_e = n_e T_e$",
    ('momentum', 'source', 'b2stbm_smo_bal', None):
        r"$S_{bm}$: application-specific parallel momentum source" "\n"
        r"(from an external code)",
    ('momentum', 'source', 'ext_smo_bal', None):
        r"$S_{ext}$: external parallel momentum source" "\n"
        r"prescribed in the input",
    # force, sources (the rest as the momentum)
    ('force', 'source', 'viscous_pol', None):
        r"$S = -\nabla_\theta\cdot\left(\Pi^{vis}_{a,\theta} +"
        r" \Pi^{hyb}_{a,\theta}\right)$" "\n"
        r"net inflow of the poloidal viscous momentum flux (with its" "\n"
        r"hybrid-scheme correction), as a force",
    ('force', 'source', 'viscous_rad', None):
        r"$S = -\nabla_r\cdot\left(\Pi^{vis}_{a,r} +"
        r" \Pi^{hyb}_{a,r}\right)$" "\n"
        r"net inflow of the radial viscous momentum flux (anomalous" "\n"
        r"viscosity, with its hybrid-scheme correction), as a force",
    ('force', 'source', 'ions', None):
        r"$\sum_{\mathrm{cells}}\frac{-\nabla\cdot\Pi_\theta}{n_a V} +"
        r" \Delta\left(\frac{\Pi_\theta}{n_a V}\right)_{\mathrm{edges}}$"
        r"" "\n"
        r"convected momentum per ion: the cells against the edges of the" "\n"
        r"slice (variation of the ions $n_a V$ of the cells), and the flux"
        r" through the walls",
    # totpress, poloidal fluxes
    ('totpress', 'flux', 'fmo_flua', None):
        r"$p_{dyn} = \sum_a\Pi_{a,\theta}S_\theta/A_\parallel \approx"
        r" \sum_a m_a n_a u_{\parallel a}^2$" "\n"
        r"dynamic pressure: convected ion momentum per parallel area" "\n"
        r"$A_\parallel = S_\theta b_\theta$",
    ('totpress', 'flux', 'pe', None):
        r"$p_e = n_e T_e$ on the downstream end faces of the flux tubes" "\n"
        r"upstream: $p_e$ downstream plus the integrated"
        r" $-\nabla_\parallel p_e\,\Delta s_\parallel$," "\n"
        r"so that each flux tube balances",
    ('totpress', 'flux', 'pi', None):
        r"$p_i = T_i\sum_a n_a$ (ions) on the downstream end faces of"
        r" the flux tubes" "\n"
        r"upstream: $p_i$ downstream plus the integrated"
        r" $-\nabla_\parallel p_i\,\Delta s_\parallel$," "\n"
        r"so that each flux tube balances",
    # totpress, sources
    ('totpress', 'source', 'b2sifr (b2sigp_style 1)', None):
        r"$\Delta s_\parallel\sum_a\left(S_{fr,i} + S_{\hat E} +"
        r" S_{th,e} + S_{th,i}\right)_a$" "\n"
        r"friction, $\hat E$ and thermal forces of b2sigp_style 1," "\n"
        r"summed over the ion species",
    ('totpress', 'source', 'b2sifr (b2sigp_style 2)', None):
        r"$\Delta s_\parallel\sum_a\left(S_{fr,e} + S_{fr,i} + S_{th,e}"
        r" + S_{th,i}\right)_a$" "\n"
        r"electron and ion friction and thermal forces of b2sigp_style 2," "\n"
        r"summed over the ion species",
    ('totpress', 'source', 'geometric term', None):
        r"$-p_{dyn}\,\nabla_\parallel\ln A_\parallel\,\Delta"
        r" s_\parallel$, $p_{dyn} = \sum_a m_a n_a u_{\parallel a}^2$" "\n"
        r"change of the parallel area $A_\parallel \propto 1/B$ along the"
        r" tube",
    ('totpress', 'source', 'raddiv', 'Net radial convected momentum'):
        r"$-\Delta s_\parallel\sum_a\nabla_r\cdot\left(m_a u_{\parallel"
        r" a}\Gamma_{a,r}\right)$" "\n"
        r"net inflow of the radial component of the convected ion"
        r" momentum," "\n"
        r"per parallel area ($\Delta s_\parallel = V/A_\parallel$: parallel"
        r" length of the cell)",
    ('totpress', 'source', 'raddiv', 'Net radial viscous flux'):
        r"$\Delta s_\parallel\sum_a\nabla_r\cdot\left(\eta^{AN}_a\nabla_r"
        r" u_{\parallel a}\right)$" "\n"
        r"net inflow of the radial component of the viscous momentum flux" "\n"
        r"(anomalous viscosity), per parallel area ($\Delta s_\parallel ="
        r" V/A_\parallel$)",
    ('totpress', 'source', 'raddiv', 'Net radial hybrid flux'):
        r"$-\Delta s_\parallel\sum_a\nabla_r\cdot\Pi^{hyb}_{a,r}$" "\n"
        r"net inflow of the radial component of the hybrid-scheme"
        r" correction" "\n"
        r"(numerical), per parallel area ($\Delta s_\parallel ="
        r" V/A_\parallel$)",
    ('totpress', 'source', 'raddiv', 'Viscous flux divergence'):
        r"$\Delta s_\parallel\sum_a\nabla_\theta\cdot\left(\eta_{a,\theta"
        r"}\nabla_\theta u_{\parallel a}\right) \approx"
        r" \nabla_\parallel\left(\frac{4}{3}\eta^{CL}_\parallel\nabla_\pa"
        r"rallel u_\parallel\right)\Delta s_\parallel$" "\n"
        r"parallel viscous force: net inflow of the poloidal viscous"
        r" flux per" "\n"
        r"parallel area, $\eta_{a,\theta} = \eta^{AN}_a +"
        r" \frac{4}{3}\eta^{CL}_{\parallel a}b_\theta^2$",
    ('totpress', 'source', 'raddiv', 'Hybrid flux divergence'):
        r"$-\Delta s_\parallel\sum_a\nabla_\theta\cdot\Pi^{hyb}_{a,\theta"
        r"}$" "\n"
        r"net inflow of the poloidal hybrid-scheme correction"
        r" (numerical) per" "\n"
        r"parallel area",
    ('totpress', 'source', 'walls',
     'Dynamic pressure through the sides and walls'):
        r"$\sum_f \pm\,p_{dyn,f}$, $p_{dyn} ="
        r" \sum_a\Pi_{a,\theta}S_\theta/A_\parallel \approx \sum_a m_a"
        r" n_a u_{\parallel a}^2$" "\n"
        r"dynamic pressure into the slice through its faces $f$ other"
        r" than the" "\n"
        r"slice edges: targets, walls and sides of the volume",
    ('totpress', 'source', 'walls', 'Electron static pressure on the walls'):
        r"$\sum_{\mathrm{slice}}(-\nabla_\parallel p_e)\,\Delta"
        r" s_\parallel - (p_{e,\mathrm{in}} -"
        r" p_{e,\mathrm{out}})_{\mathrm{edges}}$" "\n"
        r"static pressure of the flux tubes ending on targets and walls in"
        r" the slice",
    ('totpress', 'source', 'walls', 'Ion static pressure on the walls'):
        r"$\sum_{\mathrm{slice}}(-\nabla_\parallel p_i)\,\Delta"
        r" s_\parallel - (p_{i,\mathrm{in}} -"
        r" p_{i,\mathrm{out}})_{\mathrm{edges}}$" "\n"
        r"static pressure of the flux tubes ending on targets and walls"
        r" in the slice," "\n"
        r"with $p_i = T_i\sum_a n_a$ (ions)",
    ('totpress', 'source', 'b2stel_smq_ion_bal', None):
        r"$\Delta s_\parallel\sum_a S_{I,a} = m_i n_e n_0\langle\sigma"
        r" v\rangle^{ion}_0 u_{\parallel 0}\,\Delta s_\parallel$" "\n"
        r"ionisation of the B2.5 fluid neutrals into ions (the transfers"
        r" between" "\n"
        r"charge states cancel); $\Delta s_\parallel = V/A_\parallel$:"
        r" parallel length of the cell",
    ('totpress', 'source', 'b2stel_smq_rec_bal', None):
        r"$\Delta s_\parallel\sum_a S_{R,a} = -m_i n_e n_1\langle\sigma"
        r" v\rangle^{rec}_1 u_{\parallel 1}\,\Delta s_\parallel$" "\n"
        r"momentum of the singly charged ions recombining into B2.5 fluid" "\n"
        r"neutrals (the transfers between charge states cancel)",
    ('totpress', 'source', 'b2stcx_smq_bal', None):
        r"$\Delta s_\parallel\sum_a S_{CX,a} \approx m_i n_0"
        r" n_1\langle\sigma v\rangle_{cx}(u_{\parallel 0} - u_{\parallel"
        r" 1})\,\Delta s_\parallel$" "\n"
        r"charge exchange with the B2.5 fluid neutrals: the new ions"
        r" bring $u_{\parallel 0}$," "\n"
        r"the singly charged ions that become neutral take $u_{\parallel 1}$"
        r" away",
    ('totpress', 'source', 'b2siav_smovh_bal', None):
        r"$S_{vh}\Delta s_\parallel ="
        r" B^{3/2}\nabla_\parallel\left(\frac{\alpha^{NEO}\tilde\tau_i}{B"
        r"^2}\nabla_\parallel\left(B^{1/2}\tilde q_{\parallel"
        r" i}\right)\right)\Delta s_\parallel$" "\n"
        r"heat-flux part of the neoclassical parallel viscosity of the"
        r" main ions" "\n"
        r"(closed surfaces), per parallel area ($\Delta s_\parallel ="
        r" V/A_\parallel$)",
    ('totpress', 'source', 'b2siav_smovv_bal', None):
        r"$S_{vv}\Delta s_\parallel = B^{1/2}u_{\parallel"
        r" i}\nabla_\theta\cdot\left(\frac{4}{3}\eta^{CL}_{i,\theta}B^{-1"
        r"/2}\nabla_\theta\ln\left(R\,B^{1/2}\right)\right)\Delta"
        r" s_\parallel$" "\n"
        r"residual classical parallel viscosity of the main ions ($B$,"
        r" $R$ varying)," "\n"
        r"per parallel area ($\Delta s_\parallel = V/A_\parallel$)",
    ('totpress', 'source', 'b2siav_smovi_bal', None):
        r"$\Delta s_\parallel\sum_a S_{vi,a}$: cross-ion viscous stress"
        r" (Zhdanov closure)" "\n"
        r"$S_{vi,a} = \frac{4}{3}B^{3/2}\nabla_\parallel\left(\frac{\eta^"
        r"{CL}_{\parallel a}}{\rho^{rel}_a"
        r" B^2}\nabla_\parallel\left(B^{1/2}\sum_{b\neq a}\rho^{rel}_b"
        r" u_{\parallel b}\right)\right)$" "\n"
        r"per parallel area ($\Delta s_\parallel = V/A_\parallel$)",
    ('totpress', 'source', 'b2sicf_smo_bal', None):
        r"$\Delta s_\parallel\sum_a m_a n_a u_{\parallel"
        r" a}^2\,\nabla_\parallel\ln R$" "\n"
        r"centrifugal force of the ion flow ($R$: major radius), per"
        r" parallel" "\n"
        r"area ($\Delta s_\parallel = V/A_\parallel$)",
    ('totpress', 'source', 'b2sian_smo_bal', None):
        r"$-\Delta s_\parallel\sum_a"
        r" j^{AN}_{a,r}\frac{B\,B_\theta}{B_\varphi}$" "\n"
        r"toroidal $j\times B$ force of the radial anomalous current, as"
        r" parallel" "\n"
        r"momentum per parallel area ($\Delta s_\parallel = V/A_\parallel$)",
    ('totpress', 'source', 'b2stbm_smo_bal', None):
        r"$\Delta s_\parallel\sum_a S_{bm,a}$: application-specific"
        r" momentum source (external code)," "\n"
        r"per parallel area",
    ('totpress', 'source', 'ext_smo_bal', None):
        r"$\Delta s_\parallel\sum_a S_{ext,a}$: external momentum source"
        r" from the input," "\n"
        r"per parallel area ($\Delta s_\parallel = V/A_\parallel$)",
    # heat, poloidal fluxes
    ('heat', 'flux', 'fhe_32', None):
        r"$q_{e,\theta} = \frac{3}{2}\,T_e\,\Gamma_{e,\theta}$,"
        r" $\Gamma_{e,\theta} = b_\theta n_e u_{\parallel e} + \sum_a"
        r" Z_a\Gamma^{\perp}_{a,\theta}$" "\n"
        r"with $n_e u_{\parallel e} = \sum_a Z_a n_a u_{\parallel a} -"
        r" j_\parallel/e$;" "\n"
        r"$\Gamma^{\perp}_a$: $E\times B$ drift, anomalous diffusion and"
        r" pinch",
    ('heat', 'flux', 'fhe_52', None):
        r"$q_{e,\theta} = \frac{5}{2}\,T_e\,\Gamma^{\mathrm{dif}}_{e,\the"
        r"ta}$, $\Gamma^{\mathrm{dif}}_{e,\theta} = -\sum_a"
        r" Z_a(D_{n,a}\nabla_\theta n_a + D_{p,a}\nabla_\theta p_a)$" "\n"
        r"diffusive part of the particle flux, carrying $\frac{5}{2}T_e$",
    ('heat', 'flux', 'fhe_cond', None):
        r"$q_{e,\theta} = -\kappa_e^{\parallel}\,b_\theta\nabla_\parallel"
        r" T_e - n_e\chi_e^{\perp}\,\nabla_\theta T_e$" "\n"
        r"$\kappa_e^{\parallel} \propto T_e^{5/2}$: Spitzer-Härm"
        r" conductivity, $\chi_e^{\perp}$: anomalous diffusivity",
    ('heat', 'flux', 'fhe_thermj', None):
        r"$q_{e,\theta} = -c_{071}\,\frac{T_e}{e}\,b_\theta\,j_\parallel$"
        r", $c_{071} \approx 0.71$ ($Z_{\mathrm{eff}}$ dependent)" "\n"
        r"heat carried by the parallel current (thermoelectric effect)",
    ('heat', 'flux', 'fhe_dia', None):
        r"$q_{e,\theta} = \frac{5}{2}\,T_e\,n_e"
        r" V^{\mathrm{dia}}_{e,\theta} = -\frac{5}{2}\,\frac{n_e"
        r" T_e^2}{e}\,B_\varphi\,\nabla_r\left(\frac{1}{B^2}\right)$" "\n"
        r"diamagnetic heat flux without its divergence-free part",
    ('heat', 'flux', 'fhe_ecrb', None):
        r"$q_{e,\theta} = \frac{3}{2}\,T_e\,n_e V_{E,\theta}$,"
        r" $V_{E,\theta} = -\frac{B_\varphi}{B^2}\,\nabla_r\Phi$" "\n"
        r"heat convected by the $E\times B$ drift",
    ('heat', 'flux', 'fhe_strange', None):
        r"$q_{e,\theta} = V^{\mathrm{str}}_{e,\theta}\,n_e T_e$" "\n"
        r"$V^{\mathrm{str}}$: anomalous heat convection velocity",
    ('heat', 'flux', 'fhe_pschused', None):
        r"$q_{e,\theta} = \frac{5}{2}\,\frac{B_\varphi}{e}\left(\frac{1}{"
        r"B^2} - \frac{1}{\langle B^2\rangle}\right)\nabla_r(n_e T_e^2)$" "\n"
        r"Pfirsch-Schlüter heat flux (in place of the diamagnetic one);" "\n"
        r"$\langle B^2\rangle$: average of $B^2$ over the core",
    ('heat', 'flux', 'fhi_32', None):
        r"$q_{i,\theta} = \frac{3}{2}\,T_i\sum_a\Gamma_{a,\theta}$,"
        r" $\Gamma_{a,\theta} = b_\theta n_a u_{\parallel a} +"
        r" \Gamma^{\perp}_{a,\theta}$" "\n"
        r"sum over the ions and fluid neutrals; $\Gamma^{\perp}_a$:"
        r" $E\times B$ drift," "\n"
        r"anomalous diffusion and pinch",
    ('heat', 'flux', 'fhi_52', None):
        r"$q_{i,\theta} = \frac{5}{2}\,T_i\sum_a\Gamma^{\mathrm{dif}}_{a,"
        r"\theta}$, $\Gamma^{\mathrm{dif}}_{a,\theta} ="
        r" -D_{n,a}\nabla_\theta n_a - D_{p,a}\nabla_\theta p_a$" "\n"
        r"diffusive part of the particle fluxes, carrying $\frac{5}{2}T_i$",
    ('heat', 'flux', 'fhi_cond', None):
        r"$q_{i,\theta} = -\kappa_i^{\parallel}\,b_\theta\nabla_\parallel"
        r" T_i - \sum_a n_a\chi_a^{\perp}\,\nabla_\theta T_i$" "\n"
        r"$\kappa_i^{\parallel} \propto T_i^{5/2}$: classical conductivity,"
        r" $\chi_a^{\perp}$: anomalous diffusivity",
    ('heat', 'flux', 'fhi_dia', None):
        r"$q_{i,\theta} = \frac{5}{2}\,T_i\sum_a n_a"
        r" V^{\mathrm{dia}}_{a,\theta} = \frac{5}{2}\sum_a\frac{n_a"
        r" T_i^2}{Z_a e}\,B_\varphi\,\nabla_r\left(\frac{1}{B^2}\right)$" "\n"
        r"diamagnetic heat flux without its divergence-free part",
    ('heat', 'flux', 'fhi_ecrb', None):
        r"$q_{i,\theta} = \frac{3}{2}\,T_i\sum_a n_a V_{E,\theta}$,"
        r" $V_{E,\theta} = -\frac{B_\varphi}{B^2}\,\nabla_r\Phi$" "\n"
        r"heat convected by the $E\times B$ drift of the ions",
    ('heat', 'flux', 'fhi_strange', None):
        r"$q_{i,\theta} = V^{\mathrm{str}}_{i,\theta}\,n_i T_i$" "\n"
        r"$V^{\mathrm{str}}$: anomalous heat convection velocity",
    ('heat', 'flux', 'fhi_pschused', None):
        r"$q_{i,\theta} = -\frac{5}{2}\sum_a\frac{B_\varphi}{Z_a"
        r" e}\left(\frac{1}{B^2} - \frac{1}{\langle"
        r" B^2\rangle}\right)\nabla_r(n_a T_i^2)$" "\n"
        r"Pfirsch-Schlüter heat flux (in place of the diamagnetic one);" "\n"
        r"$\langle B^2\rangle$: average of $B^2$ over the core",
    ('heat', 'flux', 'fhi_inert', None):
        r"$q_{i,\theta} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{in}}_\th"
        r"eta$, $j^{\mathrm{in}}_\theta ="
        r" \frac{B_\varphi}{2}\nabla_r\left(\frac{1}{B^2}\right)\sum_a"
        r" m_a n_a u_{\parallel a}^2$" "\n"
        r"heat carried by the inertia (centrifugal drift) current",
    ('heat', 'flux', 'fhi_vispar', None):
        r"$q_{i,\theta} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{vis}\par"
        r"allel}_\theta$, $j^{\mathrm{vis}\parallel}_\theta ="
        r" -\frac{B_\varphi}{3\sqrt{B}}\nabla_r\left(\frac{1}{B^2}\right)"
        r"\eta_i^{\parallel}\nabla_\parallel(\sqrt{B}\,u_{\parallel i})$" "\n"
        r"heat carried by the parallel viscosity current of the main ions",
    ('heat', 'flux', 'fhi_anml', None):
        r"$q_{i,\theta} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{AN}}_\th"
        r"eta$, $j^{\mathrm{AN}}_\theta ="
        r" -\sigma^{\mathrm{AN}}\,\nabla_\theta\Phi$" "\n"
        r"heat carried by the anomalous current (anomalous conductivity)",
    ('heat', 'flux', 'fhi_kevis', None):
        r"$q_{i,\theta} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\kappa,\mathrm{R"
        r"S}}_\theta$, $j^{\kappa,\mathrm{RS}}_\theta ="
        r" \left[\frac{\mathbf{b}}{B}\times\nabla\left(\frac{2}{3}n\kappa"
        r"\right)\right]_\theta$" "\n"
        r"heat carried by the Reynolds-stress current of the turbulence" "\n"
        r"($\kappa$) model",
    ('heat', 'flux', 'fhi_visq', None):
        r"$q_{i,\theta} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{visq}}_"
        r"\theta$, $j^{\mathrm{visq}}_\theta ="
        r" -0.24\,\alpha^{\mathrm{NEO}}\tilde{\tau}_i\frac{B_\varphi}{\sq"
        r"rt{B}}\nabla_r\left(\frac{1}{B^2}\right)\nabla_\parallel(\sqrt{"
        r"B}\,q_{i\parallel})$" "\n"
        r"heat carried by the heat-flux viscosity current of the main ions",
    ('heat', 'flux', 'fhi_visper', None):
        r"$q_{i,\theta} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{vis}\per"
        r"p}_\theta = 0$" "\n"
        r"the perpendicular viscosity current has no poloidal component",
    ('heat', 'flux', 'fhi_vzh', None):
        r"$q_{i,\theta} = b_\theta\,T_i\sum_a n_a\sum_\beta"
        r" c^{(h_w)}_{\beta a}(u_{\parallel a} -"
        r" \overline{u}_{\parallel\beta})$" "\n"
        r"velocity-dependent ion heat flux of the Zhdanov closure" "\n"
        r"(relative parallel velocities of the ion species)",
    # heat, radial fluxes
    ('heat', 'radial', 'fhe_32', None):
        r"$q_{e,r} = \frac{3}{2}\,T_e\,\Gamma_{e,r}$, $\Gamma_{e,r} ="
        r" \sum_a Z_a\Gamma_{a,r}$" "\n"
        r"$\Gamma_{a,r}$: anomalous diffusion and pinch, $E\times B$ drift",
    ('heat', 'radial', 'fhe_52', None):
        r"$q_{e,r} = \frac{5}{2}\,T_e\,\Gamma^{\mathrm{dif}}_{e,r}$,"
        r" $\Gamma^{\mathrm{dif}}_{e,r} = -\sum_a Z_a(D_{n,a}\nabla_r"
        r" n_a + D_{p,a}\nabla_r p_a)$" "\n"
        r"anomalous diffusion flux, carrying $\frac{5}{2}T_e$",
    ('heat', 'radial', 'fhe_cond', None):
        r"$q_{e,r} = -n_e\chi_e^{\perp}\,\nabla_r T_e$" "\n"
        r"anomalous radial heat conduction",
    ('heat', 'radial', 'fhe_thermj', None):
        r"$q_{e,r} = \alpha_{e,r}\,T_e\,\hat{E}_r$, $\hat{E}_r ="
        r" \frac{\nabla_r p_e}{e n_e} - \nabla_r\Phi$" "\n"
        r"anomalous thermoelectric heat flux, $\hat{E}$: effective electric"
        r" field",
    ('heat', 'radial', 'fhe_dia', None):
        r"$q_{e,r} = \frac{5}{2}\,T_e\,n_e V^{\mathrm{dia}}_{e,r} ="
        r" \frac{5}{2}\,\frac{n_e"
        r" T_e^2}{e}\,B_\varphi\,\nabla_\theta\left(\frac{1}{B^2}\right)$" "\n"
        r"diamagnetic heat flux without its divergence-free part",
    ('heat', 'radial', 'fhe_ecrb', None):
        r"$q_{e,r} = \frac{3}{2}\,T_e\,n_e V_{E,r}$, $V_{E,r} ="
        r" \frac{B_\varphi}{B^2}\,\nabla_\theta\Phi$" "\n"
        r"heat convected by the $E\times B$ drift",
    ('heat', 'radial', 'fhe_strange', None):
        r"$q_{e,r} = V^{\mathrm{str}}_{e,r}\,n_e T_e$" "\n"
        r"$V^{\mathrm{str}}$: anomalous heat convection velocity",
    ('heat', 'radial', 'fhe_pschused', None):
        r"$q_{e,r} = -\frac{5}{2}\,\frac{B_\varphi}{e}\left(\frac{1}{B^2}"
        r" - \frac{1}{\langle B^2\rangle}\right)\nabla_\theta(n_e T_e^2)$" "\n"
        r"Pfirsch-Schlüter heat flux (in place of the diamagnetic one);" "\n"
        r"$\langle B^2\rangle$: average of $B^2$ over the core",
    ('heat', 'radial', 'fhi_32', None):
        r"$q_{i,r} = \frac{3}{2}\,T_i\sum_a\Gamma_{a,r}$" "\n"
        r"sum over the ions and fluid neutrals; $\Gamma_{a,r}$: anomalous" "\n"
        r"diffusion and pinch, $E\times B$ drift",
    ('heat', 'radial', 'fhi_52', None):
        r"$q_{i,r} = \frac{5}{2}\,T_i\sum_a\Gamma^{\mathrm{dif}}_{a,r}$,"
        r" $\Gamma^{\mathrm{dif}}_{a,r} = -D_{n,a}\nabla_r n_a -"
        r" D_{p,a}\nabla_r p_a$" "\n"
        r"anomalous diffusion fluxes, carrying $\frac{5}{2}T_i$",
    ('heat', 'radial', 'fhi_cond', None):
        r"$q_{i,r} = -\sum_a n_a\chi_a^{\perp}\,\nabla_r T_i$" "\n"
        r"anomalous radial heat conduction",
    ('heat', 'radial', 'fhi_dia', None):
        r"$q_{i,r} = \frac{5}{2}\,T_i\sum_a n_a V^{\mathrm{dia}}_{a,r} ="
        r" -\frac{5}{2}\sum_a\frac{n_a T_i^2}{Z_a"
        r" e}\,B_\varphi\,\nabla_\theta\left(\frac{1}{B^2}\right)$" "\n"
        r"diamagnetic heat flux without its divergence-free part",
    ('heat', 'radial', 'fhi_ecrb', None):
        r"$q_{i,r} = \frac{3}{2}\,T_i\sum_a n_a V_{E,r}$, $V_{E,r} ="
        r" \frac{B_\varphi}{B^2}\,\nabla_\theta\Phi$" "\n"
        r"heat convected by the $E\times B$ drift of the ions",
    ('heat', 'radial', 'fhi_strange', None):
        r"$q_{i,r} = V^{\mathrm{str}}_{i,r}\,n_i T_i$" "\n"
        r"$V^{\mathrm{str}}$: anomalous heat convection velocity",
    ('heat', 'radial', 'fhi_pschused', None):
        r"$q_{i,r} = \frac{5}{2}\sum_a\frac{B_\varphi}{Z_a"
        r" e}\left(\frac{1}{B^2} - \frac{1}{\langle"
        r" B^2\rangle}\right)\nabla_\theta(n_a T_i^2)$" "\n"
        r"Pfirsch-Schlüter heat flux (in place of the diamagnetic one);" "\n"
        r"$\langle B^2\rangle$: average of $B^2$ over the core",
    ('heat', 'radial', 'fhi_inert', None):
        r"$q_{i,r} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{in}}_r$,"
        r" $j^{\mathrm{in}}_r ="
        r" -\frac{B_\varphi}{2}\nabla_\theta\left(\frac{1}{B^2}\right)\su"
        r"m_a m_a n_a u_{\parallel a}^2$" "\n"
        r"heat carried by the inertia (centrifugal drift) current",
    ('heat', 'radial', 'fhi_vispar', None):
        r"$q_{i,r} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{vis}\parallel"
        r"}_r$, $j^{\mathrm{vis}\parallel}_r ="
        r" \frac{B_\varphi}{3\sqrt{B}}\nabla_\theta\left(\frac{1}{B^2}\ri"
        r"ght)\eta_i^{\parallel}\nabla_\parallel(\sqrt{B}\,u_{\parallel"
        r" i})$" "\n"
        r"heat carried by the parallel viscosity current of the main ions",
    ('heat', 'radial', 'fhi_anml', None):
        r"$q_{i,r} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{AN}}_r$,"
        r" $j^{\mathrm{AN}}_r = -\sigma^{\mathrm{AN}}\,\nabla_r\Phi$" "\n"
        r"heat carried by the anomalous current (anomalous conductivity)",
    ('heat', 'radial', 'fhi_kevis', None):
        r"$q_{i,r} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\kappa,\mathrm{RS}}_r"
        r"$, $j^{\kappa,\mathrm{RS}}_r ="
        r" \left[\frac{\mathbf{b}}{B}\times\nabla\left(\frac{2}{3}n\kappa"
        r"\right)\right]_r - \frac{1}{B}\nabla_r(\eta_E\nabla_r V_E)$" "\n"
        r"heat carried by the Reynolds-stress current of the turbulence" "\n"
        r"($\kappa$) model",
    ('heat', 'radial', 'fhi_visq', None):
        r"$q_{i,r} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{visq}}_r$,"
        r" $j^{\mathrm{visq}}_r ="
        r" 0.24\,\alpha^{\mathrm{NEO}}\tilde{\tau}_i\frac{B_\varphi}{\sqr"
        r"t{B}}\nabla_\theta\left(\frac{1}{B^2}\right)\nabla_\parallel(\s"
        r"qrt{B}\,q_{i\parallel})$" "\n"
        r"heat carried by the heat-flux viscosity current of the main ions",
    ('heat', 'radial', 'fhi_visper', None):
        r"$q_{i,r} = \frac{3}{2}\,\frac{T_i}{e}\,j^{\mathrm{vis}\perp}_r$"
        r", $j^{\mathrm{vis}\perp}_r ="
        r" -\sum_a\frac{1}{B}\nabla_r\left(\frac{\eta_a^{\perp}}{4}\nabla"
        r"_r V_{a\perp}\right)$" "\n"
        r"heat carried by the perpendicular viscosity current," "\n"
        r"$V_{a\perp} = -\frac{\nabla_r\Phi}{B} - \frac{\nabla_r(n_a"
        r" T_i)}{Z_a e B n_a}$",
    ('heat', 'radial', 'fhi_vzh', None):
        r"$q_{i,r} = 0$" "\n"
        r"the velocity-dependent heat flux is parallel: no radial component",
    # heat, sources
    ('heat', 'source', 'b2sihs_diae_bal', None):
        r"$Q^{\mathrm{dia}}_e = \frac{5}{2e}\left[\nabla(n_e"
        r" T_e^2)\times\nabla\left(\frac{B_\varphi}{B^2}\right)\right]_\v"
        r"arphi$" "\n"
        r"divergence of the electron diamagnetic heat flux as a volume source",
    ('heat', 'source', 'b2sihs_divue_bal', None):
        r"$Q_e = -p_e\,\nabla\cdot(u_{\parallel e}\,\mathbf{b})$, $n_e"
        r" u_{\parallel e} = \sum_a Z_a n_a u_{\parallel a} -"
        r" j_\parallel/e$" "\n"
        r"compression work of the parallel electron flow",
    ('heat', 'source', 'b2sihs_exbe_bal', None):
        r"$Q_e = -p_e\,\nabla\cdot\mathbf{V}_E$" "\n"
        r"$\nabla\cdot\mathbf{V}_E \approx"
        r" B_\varphi\left(\nabla_\theta\Phi\,\nabla_r\frac{1}{B^2} -"
        r" \nabla_r\Phi\,\nabla_\theta\frac{1}{B^2}\right)$" "\n"
        r"compression by the $E\times B$ drift (electrons)",
    ('heat', 'source', 'b2sihs_joule_bal', None):
        r"$Q_{Fei} = u_{\parallel e}\sum_a\left(R^{\mathrm{fr}}_{ea} +"
        r" R^{T}_{ea}\right)$" "\n"
        r"$R_{ea}$: friction and thermal force of the electrons on the ions"
        r" $a$",
    ('heat', 'source', 'b2npht_shei_bal', None):
        r"$Q_\Delta = 3\,n_e\sum_a\frac{m_e}{m_a}\,\nu_{ea}\,(T_e -"
        r" T_i)$, $\nu_{ea} \propto Z_a^2 n_a\ln\Lambda/T_e^{3/2}$" "\n"
        r"electron-ion collisional energy exchange (equipartition):" "\n"
        r"from the electrons to the ions when $T_e > T_i$",
    ('heat', 'source', 'b2stel_rqrad_bal', None):
        r"$Q_{\mathrm{line}} = -n_e\sum_a n_a\,L^{\mathrm{line}}_a(T_e,"
        r" n_e)$" "\n"
        r"line radiation of the B2.5 species ($L_a$: radiated power"
        r" coefficient)",
    ('heat', 'source', 'b2stel_rqbrm_bal', None):
        r"$Q_{\mathrm{brm}} = -n_e\sum_a n_a\,L^{\mathrm{brm}}_a$,"
        r" $L^{\mathrm{brm}}_a \propto Z_a^2\sqrt{T_e}$" "\n"
        r"bremsstrahlung of the charged B2.5 species",
    ('heat', 'source', 'b2stel_iz_bal', None):
        r"$Q_{\mathrm{iz}} = -n_e\sum_a n_a\,\langle\sigma"
        r" v\rangle^{\mathrm{iz}}_a\,E^{\mathrm{iz}}_a$" "\n"
        r"electron energy spent on ionisation of the B2.5 species",
    ('heat', 'source', 'b2stel_rc_bal', None):
        r"$Q_{\mathrm{rc}} = n_e\sum_a n_a\left(\langle\sigma"
        r" v\rangle^{\mathrm{rc}}_aE^{\mathrm{iz}}_{a-1} -"
        r" L^{\mathrm{rc}}_a\right)$" "\n"
        r"electron energy of recombination: cooling rate"
        r" $L^{\mathrm{rc}}_a$ and" "\n"
        r"the ionisation energy given back to the electrons",
    ('heat', 'source', 'b2stel_shi_ion_bal', None):
        r"$Q^{(i)}_I = n_e\sum_a n_a\langle\sigma"
        r" v\rangle^{\mathrm{iz}}_a\,\frac{m_a +"
        r" m_{a+1}}{4}\,(u_{\parallel a} - u_{\parallel a+1})^2$" "\n"
        r"ion heat from ionisation: relative kinetic energy of the"
        r" ionised" "\n"
        r"particles (B2.5 rates)",
    ('heat', 'source', 'b2stel_shi_rec_bal', None):
        r"$Q^{(i)}_R = n_e\sum_a n_a\langle\sigma"
        r" v\rangle^{\mathrm{rc}}_a\,\frac{m_a +"
        r" m_{a-1}}{4}\,(u_{\parallel a} - u_{\parallel a-1})^2$" "\n"
        r"ion heat from recombination: relative kinetic energy of the" "\n"
        r"recombined particles (B2.5 rates)",
    ('heat', 'source', 'b2stcx_shi_bal', None):
        r"$Q_{\mathrm{cx}} = \sum_{a,b} n_a n_b\langle\sigma"
        r" v\rangle^{\mathrm{cx}}_{ab}\,\frac{\overline{m}}{2}\left[(\Del"
        r"ta u_{\parallel a})^2 + (\Delta u_{\parallel b})^2\right]$" "\n"
        r"B2.5 charge exchange $a + b \rightarrow (a-1) + (b+1)$:"
        r" relative kinetic" "\n"
        r"energy of the exchanged particles ($\overline{m}$: mean mass of"
        r" the pair)",
    ('heat', 'source', 'b2sihs_diaa_bal', None):
        r"$Q^{\mathrm{dia}}_i ="
        r" -\frac{5}{2e}\sum_a\frac{1}{Z_a}\left[\nabla(n_a"
        r" T_i^2)\times\nabla\left(\frac{B_\varphi}{B^2}\right)\right]_\v"
        r"arphi$" "\n"
        r"divergence of the ion diamagnetic heat flux as a volume source",
    ('heat', 'source', 'b2sihs_divua_bal', None):
        r"$Q_i = -T_i\sum_a n_a\,\nabla\cdot(u_{\parallel"
        r" a}\,\mathbf{b})$" "\n"
        r"compression work of the parallel flows of the ions and fluid"
        r" neutrals",
    ('heat', 'source', 'b2sihs_exba_bal', None):
        r"$Q_i = -T_i\sum_{Z_a \neq 0} n_a\,\nabla\cdot\mathbf{V}_E$" "\n"
        r"$\nabla\cdot\mathbf{V}_E \approx"
        r" B_\varphi\left(\nabla_\theta\Phi\,\nabla_r\frac{1}{B^2} -"
        r" \nabla_r\Phi\,\nabla_\theta\frac{1}{B^2}\right)$" "\n"
        r"compression by the $E\times B$ drift (ions)",
    ('heat', 'source', 'b2sihs_visa_bal', None):
        r"$Q_{\mathrm{vis}} = \sum_a\left[\eta_a^{\parallel}(\nabla_\para"
        r"llel u_{\parallel a})^2 + \eta_a^{\perp}(\nabla_r u_{\parallel"
        r" a})^2\right]$" "\n"
        r"viscous heating by the parallel flows (classical parallel and" "\n"
        r"anomalous perpendicular viscosity)",
    ('heat', 'source', 'b2sihs_fraa_bal', None):
        r"$Q_{F_{ab}} = -\sum_a u_{\parallel a}\left(R^{\mathrm{fr}}_a +"
        r" R^{T}_a\right)$" "\n"
        r"$R_a$: friction and thermal forces on the ions $a$ (electrons,"
        r" ions)",
    ('heat', 'source', 'b2stbm_she_bal', None):
        r"$Q^{\mathrm{app}}_e$: application-specific electron heat source"
        r" (external code)",
    ('heat', 'source', 'b2stbm_shi_bal', None):
        r"$Q^{\mathrm{app}}_i$: application-specific ion heat source"
        r" (external code)",
    ('heat', 'source', 'ext_she_bal', None):
        r"$Q^{\mathrm{ext}}_e$: external electron heat source prescribed"
        r" in the input" "\n"
        r"(profile sources, e.g. auxiliary heating)",
    ('heat', 'source', 'ext_shi_bal', None):
        r"$Q^{\mathrm{ext}}_i$: external ion heat source prescribed in"
        r" the input" "\n"
        r"(profile sources, e.g. auxiliary heating)",
    # toten, poloidal fluxes
    ('toten', 'flux', 'kinetic', 'Kinetic energy, convected'):
        r"$q^{\mathrm{kin}}_\theta = \sum_a\frac{1}{2}m_a u_{\parallel"
        r" a}^2\,\Gamma_{a,\theta}$, $\Gamma_{a,\theta} = b_\theta n_a"
        r" u_{\parallel a} + \Gamma^{\perp}_{a,\theta}$" "\n"
        r"$u_\parallel\times$ convected momentum flux"
        r" $-\frac{1}{2}mu_\parallel^2\times$ particle flux (ions)",
    ('toten', 'flux', 'kinetic', 'Kinetic energy, viscous'):
        r"$q^{\mathrm{kin}}_\theta = \sum_a u_{\parallel"
        r" a}\,\pi_{a,\theta}$, $\pi_{a,\theta} ="
        r" -\eta_a^{\parallel}\,b_\theta\nabla_\parallel u_{\parallel a}$" "\n"
        r"work of the viscous flux of parallel momentum (ions)",
    ('toten', 'flux', 'kinetic', 'Kinetic energy, hybrid'):
        r"$q^{\mathrm{kin}}_\theta = \sum_a u_{\parallel a}\,(\eta_a -"
        r" \eta_a^{\mathrm{eff}})\,\nabla_\theta u_{\parallel a}$" "\n"
        r"hybrid-scheme correction of the viscous momentum flux:" "\n"
        r"$\eta^{\mathrm{eff}} = \sqrt{\eta^2 + F^2/4} - |F|/2$, $F$: mass"
        r" flux through the face",
    # toten, radial fluxes
    ('toten', 'radial', 'kinetic', 'Kinetic energy, convected'):
        r"$q^{\mathrm{kin}}_r = \sum_a\frac{1}{2}m_a u_{\parallel"
        r" a}^2\,\Gamma_{a,r}$" "\n"
        r"$u_\parallel\times$ convected momentum flux"
        r" $-\frac{1}{2}mu_\parallel^2\times$ particle flux (ions)",
    ('toten', 'radial', 'kinetic', 'Kinetic energy, viscous'):
        r"$q^{\mathrm{kin}}_r = \sum_a u_{\parallel a}\,\pi_{a,r}$,"
        r" $\pi_{a,r} = -\eta_a^{\perp}\,\nabla_r u_{\parallel a}$" "\n"
        r"work of the anomalous viscous flux of parallel momentum (ions)",
    ('toten', 'radial', 'kinetic', 'Kinetic energy, hybrid'):
        r"$q^{\mathrm{kin}}_r = \sum_a u_{\parallel a}\,(\eta_a -"
        r" \eta_a^{\mathrm{eff}})\,\nabla_r u_{\parallel a}$" "\n"
        r"hybrid-scheme correction of the viscous momentum flux:" "\n"
        r"$\eta^{\mathrm{eff}} = \sqrt{\eta^2 + F^2/4} - |F|/2$, $F$: mass"
        r" flux through the face",
    # toten, sources
    ('toten', 'source', 'kinetic',
     'u × (ionisation, recombination, charge exchange)'):
        r"$\sum_a u_{\parallel a}\left(S^{\mathrm{iz}}_{m,a} +"
        r" S^{\mathrm{rc}}_{m,a} + S^{\mathrm{cx}}_{m,a}\right)$, momentum"
        r" of B2.5 atomic processes",
    ('toten', 'source', 'kinetic', 'u × (friction, thermal forces)'):
        r"$\sum_a u_{\parallel a}\left(R^{\mathrm{fr}}_a +"
        r" R^{T}_a\right)$" "\n"
        r"friction and thermal forces on the ions $a$ (electrons, other"
        r" ions):" "\n"
        r"$R^{\mathrm{fr}} \propto$ relative velocities, $R^{T} \propto"
        r" \nabla_\parallel T_e,\,\nabla_\parallel T_i$",
    ('toten', 'source', 'kinetic', 'u × viscosity'):
        r"$\sum_a u_{\parallel a}\,S^{\mathrm{vis}}_{m,a}$" "\n"
        r"work of the additional parallel viscous forces on the ions" "\n"
        r"(neoclassical and Zhdanov viscosity)",
    ('toten', 'source', 'kinetic', 'u × other momentum sources'):
        r"$\sum_a u_{\parallel a}\,S^{\mathrm{other}}_{m,a}$" "\n"
        r"centrifugal and anomalous-current forces, recycling, external," "\n"
        r"boundary and numerical momentum sources",
    ('toten', 'source', 'kinetic', 'u × (static pressure, electric field)'):
        r"$-\sum_a u_{\parallel a}\left[\nabla_\parallel(n_a T_i) + Z_a"
        r" e n_a\nabla_\parallel\Phi\right]$" "\n"
        r"work of the ion pressure gradient and the parallel electric field",
    ('toten', 'source', 'kinetic', '-mu²/2 × B2.5 particle sources'):
        r"$-\sum_a\frac{1}{2}m_a u_{\parallel a}^2\,S_{n,a}$" "\n"
        r"$S_{n,a}$: B2.5 particle sources (atomic, recycling, boundary,"
        r" external)" "\n"
        r"kinetic energy = $u_\parallel\times$ momentum"
        r" $-\frac{1}{2}mu_\parallel^2\times$ continuity",
}
