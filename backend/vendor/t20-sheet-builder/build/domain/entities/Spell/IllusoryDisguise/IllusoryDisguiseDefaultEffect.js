"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IllusoryDisguiseDefaultEffect = void 0;
const AffectableTarget_1 = require("../../Affectable/AffectableTarget");
const ManaCost_1 = require("../../ManaCost");
const SpellEffect_1 = require("../SpellEffect");
const SpellName_1 = require("../SpellName");
class IllusoryDisguiseDefaultEffect extends SpellEffect_1.SpellEffect {
    static get duration() {
        return 'scene';
    }
    static get modifierValue() {
        return 10;
    }
    constructor() {
        super({
            duration: IllusoryDisguiseDefaultEffect.duration,
            execution: 'default',
            source: SpellName_1.SpellName.illusoryDisguise,
        });
        this.baseCosts = [new ManaCost_1.ManaCost(1)];
        this.description = 'Você muda a aparência do alvo, incluindo'
            + ' seu equipamento. Isso inclui altura, peso, tom de pele, cor de cabelo,'
            + ' timbre de voz etc. O alvo recebe +10 em testes de Enganação para'
            + ' disfarce. O alvo não recebe novas habilidades (você pode ficar parecido com'
            + ' outra raça, mas não ganhará as habilidades dela), nem modifica o equipamento'
            + ' (uma espada longa disfarçada de bordão continua funcionando e causando dano como uma espada).';
        this.affectable = new AffectableTarget_1.AffectableTarget('self');
        this.range = 'personal';
    }
}
exports.IllusoryDisguiseDefaultEffect = IllusoryDisguiseDefaultEffect;
