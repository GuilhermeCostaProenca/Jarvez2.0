"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WildEmpathy = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class WildEmpathy extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.wildEmpathy);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new Ability_1.RolePlayEffect(this.name, WildEmpathy.description),
            },
        });
    }
}
exports.WildEmpathy = WildEmpathy;
WildEmpathy.description = 'Você pode se comunicar'
    + ' com animais por meio de linguagem corporal e vocalizações.'
    + ' Você pode usar Adestramento com animais'
    + ' para mudar atitude e persuasão';
