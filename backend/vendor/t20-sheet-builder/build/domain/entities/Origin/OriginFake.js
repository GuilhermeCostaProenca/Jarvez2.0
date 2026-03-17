"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginFake = void 0;
const vitest_1 = require("vitest");
const OriginPowerName_1 = require("../Power/OriginPower/OriginPowerName");
const OriginName_1 = require("./OriginName");
class OriginFake {
    constructor() {
        this.name = OriginName_1.OriginName.acolyte;
        this.equipments = [];
        this.chosenBenefits = [];
        this.benefits = { generalPowers: [], originPower: OriginPowerName_1.OriginPowerName.churchMember, skills: [] };
        this.addToSheet = vitest_1.vi.fn();
        this.serialize = vitest_1.vi.fn();
    }
}
exports.OriginFake = OriginFake;
