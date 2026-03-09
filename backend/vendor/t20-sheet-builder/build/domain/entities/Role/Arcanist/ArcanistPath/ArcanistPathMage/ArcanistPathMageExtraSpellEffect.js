"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathMageExtraSpellEffect = void 0;
const PassiveEffect_1 = require("../../../../Ability/PassiveEffect");
const LearnSpell_1 = require("../../../../Action/LearnSpell");
const RoleAbilityName_1 = require("../../../RoleAbilityName");
const ArcanistPath_1 = require("../ArcanistPath");
class ArcanistPathMageExtraSpellEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você começa com uma magia adicional (para um total de 4)';
    }
    constructor(spell) {
        super(RoleAbilityName_1.RoleAbilityName.arcanistPath);
        this.spell = spell;
    }
    apply(transaction) {
        transaction.run(new LearnSpell_1.LearnSpell({
            payload: {
                source: ArcanistPath_1.ArcanistPathName.mage,
                spell: this.spell,
            },
            transaction,
        }));
    }
}
exports.ArcanistPathMageExtraSpellEffect = ArcanistPathMageExtraSpellEffect;
