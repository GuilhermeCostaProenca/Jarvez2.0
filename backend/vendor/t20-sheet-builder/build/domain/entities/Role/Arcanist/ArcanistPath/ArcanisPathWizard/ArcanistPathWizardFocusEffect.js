"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistPathWizardFocusEffect = void 0;
const PassiveEffect_1 = require("../../../../Ability/PassiveEffect");
const AddEquipment_1 = require("../../../../Action/AddEquipment");
const RoleAbilityName_1 = require("../../../RoleAbilityName");
const ArcanistPath_1 = require("../ArcanistPath");
class ArcanistPathWizardFocusEffect extends PassiveEffect_1.PassiveEffect {
    get description() {
        return 'Você lança magias através de um foco — uma varinha, cajado, chapéu...';
    }
    constructor(focus) {
        super(RoleAbilityName_1.RoleAbilityName.arcanistPath);
        this.focus = focus;
    }
    apply(transaction) {
        transaction.run(new AddEquipment_1.AddEquipment({
            payload: {
                equipment: this.focus.equipment,
                source: ArcanistPath_1.ArcanistPathName.wizard,
            },
            transaction,
        }));
    }
}
exports.ArcanistPathWizardFocusEffect = ArcanistPathWizardFocusEffect;
