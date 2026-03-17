"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Bomb = void 0;
const EquipmentName_1 = require("../../EquipmentName");
const EquipmentAlchemic_1 = require("../EquipmentAlchemic");
const EquipmentAlchemicCategory_1 = require("../EquipmentAlchemicCategory");
class Bomb extends EquipmentAlchemic_1.EquipmentAlchemic {
    constructor() {
        super(...arguments);
        this.alchemicCategory = EquipmentAlchemicCategory_1.EquipmentAlchemicCategory.prepared;
        this.price = 50;
        this.description = 'Uma granada rudimentar. Para usar a'
            + ' bomba, você precisa empunhá-la, gastar uma ação de'
            + ' movimento para acender seu pavio e uma ação padrão'
            + ' para arremessá-la em um ponto em alcance curto.'
            + ' Criaturas a até 3m desse ponto sofrem 6d6 pontos de'
            + ' dano de impacto (Reflexos CD Des reduz à metade).';
        this.name = EquipmentName_1.EquipmentName.bomb;
        this.isWieldable = true;
    }
}
exports.Bomb = Bomb;
