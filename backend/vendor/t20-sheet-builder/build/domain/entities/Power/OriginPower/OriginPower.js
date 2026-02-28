"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.OriginPower = void 0;
const Power_1 = require("../Power");
class OriginPower extends Power_1.Power {
    constructor(name) {
        super(name, 'origin');
        this.name = name;
    }
}
exports.OriginPower = OriginPower;
