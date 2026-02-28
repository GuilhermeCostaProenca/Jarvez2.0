"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SelfConfidence = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class SelfConfidence extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.selfConfidence);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new Ability_1.RolePlayEffect(RoleAbilityName_1.RoleAbilityName.selfConfidence, SelfConfidence.description),
            },
        });
    }
}
exports.SelfConfidence = SelfConfidence;
SelfConfidence.description = 'Você pode usar seu Carisma'
    + ' em vez de Destreza na Defesa (mas continua não podendo'
    + ' somar um atributo na Defesa quando usa armadura pesada).';
