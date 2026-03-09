"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.HornesEffect = void 0;
const Ability_1 = require("../../Ability");
const AddEquipment_1 = require("../../Action/AddEquipment");
const Inventory_1 = require("../../Inventory");
const RaceAbilityName_1 = require("../RaceAbilityName");
class HornesEffect extends Ability_1.PassiveEffect {
    constructor() {
        super(RaceAbilityName_1.RaceAbilityName.hornes);
        this.description = 'Você possui uma '
            + 'arma natural de chifres (dano 1d6, crítico x2, '
            + 'perfuração). Uma vez por rodada, quando usa a ação '
            + 'agredir para atacar com outra arma, pode gastar 1PM '
            + 'para fazer um ataque corpo-a-corpo extra com os chifres.';
    }
    apply(transaction) {
        const source = 'default';
        transaction.run(new AddEquipment_1.AddEquipment({ payload: { equipment: new Inventory_1.Horns(), source }, transaction }));
    }
}
exports.HornesEffect = HornesEffect;
