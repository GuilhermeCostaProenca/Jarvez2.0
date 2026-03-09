"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistLineageFaerieExtraSpellEffect = void 0;
const PassiveEffect_1 = require("../../../../../../Ability/PassiveEffect");
const LearnSpell_1 = require("../../../../../../Action/LearnSpell");
const errors_1 = require("../../../../../../../errors");
const Spell_1 = require("../../../../../../Spell");
const RoleAbilityName_1 = require("../../../../../RoleAbilityName");
class ArcanistLineageFaerieExtraSpellEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você aprende uma magia de 1º círculo de encantamento ou ilusão, arcana ou divina, a sua escolha.';
    }
    constructor(spell) {
        super(RoleAbilityName_1.RoleAbilityName.arcanistSupernaturalLineage);
        this.spell = spell;
        if (spell.school !== Spell_1.SpellSchool.illusion && spell.school !== Spell_1.SpellSchool.enchantment) {
            throw new errors_1.SheetBuilderError('INVALID_FAERIE_SPELL_SCHOOL');
        }
    }
    apply(transaction) {
        transaction.run(new LearnSpell_1.LearnSpell({
            payload: {
                spell: this.spell,
                source: this.source,
            },
            transaction,
        }));
    }
}
exports.ArcanistLineageFaerieExtraSpellEffect = ArcanistLineageFaerieExtraSpellEffect;
