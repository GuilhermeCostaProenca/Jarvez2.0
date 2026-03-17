"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Asset = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class Asset extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.asset);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new Ability_1.RolePlayEffect(RoleAbilityName_1.RoleAbilityName.asset, Asset.description),
            },
        });
    }
}
exports.Asset = Asset;
Asset.description = 'Você recebe um item a sua escolha'
    + ' com preço de até T$ 2.000.';
