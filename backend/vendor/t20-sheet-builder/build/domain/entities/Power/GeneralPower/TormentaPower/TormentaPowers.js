"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.TormentaPowers = void 0;
const Shell_1 = require("./Shell");
class TormentaPowers {
    static getAll() {
        return Object.values(TormentaPowers.map);
    }
}
exports.TormentaPowers = TormentaPowers;
TormentaPowers.map = {
    shell: Shell_1.Shell,
};
