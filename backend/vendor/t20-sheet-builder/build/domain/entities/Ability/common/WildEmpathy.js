"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WildEmpathy = void 0;
const AbilityEffects_1 = require("../AbilityEffects");
const RolePlayEffect_1 = require("../RolePlayEffect");
const RaceAbility_1 = require("../../Race/RaceAbility");
const RaceAbilityName_1 = require("../../Race/RaceAbilityName");
const WildEmpathyRepeatedEffect_1 = require("./WildEmpathyRepeatedEffect");
class WildEmpathy extends RaceAbility_1.RaceAbility {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.wildEmpathy);
        this.effects = new AbilityEffects_1.AbilityEffects({
            roleplay: {
                default: new RolePlayEffect_1.RolePlayEffect(RaceAbilityName_1.RaceAbilityName.wildEmpathy, WildEmpathy.effectDescription),
            },
            passive: {
                repeated: new WildEmpathyRepeatedEffect_1.WildEmpathyRepeatedEffect(),
            },
        });
    }
}
exports.WildEmpathy = WildEmpathy;
WildEmpathy.effectDescription = 'Você pode se comunicar'
    + ' com animais por meio de linguagem corporal e vocalizações.'
    + ' Você pode usar Adestramento'
    + ' para mudar atitude e'
    + ' persuasão com animais (veja'
    + ' Diplomacia, na página'
    + ' 118).';
