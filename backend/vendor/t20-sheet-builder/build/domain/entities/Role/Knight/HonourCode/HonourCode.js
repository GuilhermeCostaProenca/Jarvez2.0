"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HonourCode = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
class HonourCode extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.honourCode);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new Ability_1.RolePlayEffect(this.name, HonourCode.description),
            },
        });
    }
}
exports.HonourCode = HonourCode;
HonourCode.description = 'Cavaleiros distinguem-se'
    + ' de meros combatentes por seguir um código de conduta.'
    + ' Fazem isto para mostrar que estão acima dos'
    + ' mercenários e bandoleiros que infestam os campos'
    + ' de batalha. Você não pode atacar um oponente pelas'
    + ' costas (em termos de jogo, não pode se beneficiar do'
    + ' bônus de flanquear), caído, desprevenido ou incapaz'
    + ' de lutar. Se violar o código, você perde todos os seus'
    + ' PM e só pode recuperá-los a partir do próximo dia.'
    + ' Rebaixar-se ao nível dos covardes e desesperados'
    + ' abala a autoconfiança que eleva o cavaleiro.';
