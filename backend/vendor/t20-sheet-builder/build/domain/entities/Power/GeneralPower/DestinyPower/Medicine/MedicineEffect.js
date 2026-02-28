"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MedicineEffect = void 0;
const ActivateableAbilityEffect_1 = require("../../../../Ability/ActivateableAbilityEffect");
const GeneralPowerName_1 = require("../../GeneralPowerName");
class MedicineEffect extends ActivateableAbilityEffect_1.ActivateableAbilityEffect {
    constructor() {
        super({
            duration: 'immediate',
            execution: 'complete',
            source: GeneralPowerName_1.GeneralPowerName.medicine,
        });
        this.description = MedicineEffect.description;
        this.baseCosts = [];
    }
}
exports.MedicineEffect = MedicineEffect;
MedicineEffect.description = 'Você pode gastar uma ação completa para fazer um teste de Cura (CD 15) em uma criatura. Se você'
    + ' passar, ela recupera 1d6 PV, mais 1d6 para cada 5'
    + ' pontos pelos quais o resultado do teste exceder a CD'
    + ' (2d6 com um resultado 20, 3d6 com um resultado'
    + ' 25 e assim por diante). Você só pode usar este poder'
    + ' uma vez por dia numa mesma criatura.';
