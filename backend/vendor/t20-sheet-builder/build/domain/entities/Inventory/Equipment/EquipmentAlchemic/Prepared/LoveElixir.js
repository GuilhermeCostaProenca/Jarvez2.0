"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LoveElixir = void 0;
const EquipmentName_1 = require("../../EquipmentName");
const EquipmentAlchemic_1 = require("../EquipmentAlchemic");
const EquipmentAlchemicCategory_1 = require("../EquipmentAlchemicCategory");
class LoveElixir extends EquipmentAlchemic_1.EquipmentAlchemic {
    constructor() {
        super(...arguments);
        this.alchemicCategory = EquipmentAlchemicCategory_1.EquipmentAlchemicCategory.prepared;
        this.price = 100;
        this.description = 'Um humanoide que beba'
            + ' este líquido adocicado fica apaixonado pela primeira'
            + ' criatura que enxergar (condição enfeitiçado; Vontade'
            + ' CD Car anula). O efeito dura 1d3 dias.';
        this.name = EquipmentName_1.EquipmentName.loveElixir;
        this.isWieldable = true;
    }
}
exports.LoveElixir = LoveElixir;
