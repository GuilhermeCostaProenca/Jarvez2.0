"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MysticTattooEffect = void 0;
const Ability_1 = require("../../../Ability");
const LearnSpell_1 = require("../../../Action/LearnSpell");
const Spell_1 = require("../../../Spell");
const RaceAbilityName_1 = require("../../RaceAbilityName");
class MysticTattooEffect extends Ability_1.PassiveEffect {
    constructor(spell) {
        super(RaceAbilityName_1.RaceAbilityName.mysticTattoo);
        this.spell = spell;
        this.description = 'Você'
            + ' pode lançar uma magia de 1º'
            + ' círculo a sua escolha (atributo-'
            + ' chave Carisma). Caso'
            + ' aprenda novamente essa'
            + ' magia, seu custo diminui'
            + ' em –1 PM.';
    }
    apply(transaction) {
        transaction.run(new LearnSpell_1.LearnSpell({
            payload: {
                source: this.source,
                spell: Spell_1.SpellFactory.make(this.spell),
                needsCircle: false,
                needsSchool: false,
            },
            transaction,
        }));
    }
}
exports.MysticTattooEffect = MysticTattooEffect;
