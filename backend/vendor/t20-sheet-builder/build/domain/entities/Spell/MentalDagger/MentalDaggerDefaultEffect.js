"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MentalDaggerDefaultEffect = void 0;
const EffectAffectable_1 = require("../../Ability/EffectAffectable");
const ManaCost_1 = require("../../ManaCost");
const SpellEffect_1 = require("../SpellEffect");
const SpellName_1 = require("../SpellName");
class MentalDaggerDefaultEffect extends SpellEffect_1.SpellEffect {
    constructor() {
        super({
            execution: 'default',
            duration: 'immediate',
            source: SpellName_1.SpellName.mentalDagger,
        });
        this.description = 'Você manifesta e dispara uma adaga'
            + ' imaterial contra a mente do alvo, que sofre 2d6 pontos de dano psíquico e'
            + ' fica atordoado por uma rodada. Se passar no teste de resistência, sofre apenas'
            + ' metade do dano e evita a condição.	Uma criatura só pode ficar atordoada'
            + ' por esta magia uma vez por cena.';
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.range = 'short';
        this.affectable = new EffectAffectable_1.EffectAffectableTarget('creature', 1);
    }
}
exports.MentalDaggerDefaultEffect = MentalDaggerDefaultEffect;
