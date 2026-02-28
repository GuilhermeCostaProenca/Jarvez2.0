"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.sizes = void 0;
const SizeName_1 = require("./SizeName");
exports.sizes = {
    tiny: {
        furtivityModifier: 5,
        maneuversModifier: -5,
        name: SizeName_1.SizeName.tiny,
        occupiedSpaceInMeters: 1.5,
    },
    small: {
        furtivityModifier: 2,
        maneuversModifier: -2,
        name: SizeName_1.SizeName.small,
        occupiedSpaceInMeters: 1.5,
    },
    medium: {
        furtivityModifier: 0,
        maneuversModifier: 0,
        name: SizeName_1.SizeName.medium,
        occupiedSpaceInMeters: 1.5,
    },
    large: {
        furtivityModifier: -2,
        maneuversModifier: 2,
        name: SizeName_1.SizeName.large,
        occupiedSpaceInMeters: 3,
    },
    huge: {
        furtivityModifier: -5,
        maneuversModifier: 5,
        name: SizeName_1.SizeName.huge,
        occupiedSpaceInMeters: 4.5,
    },
    colossal: {
        furtivityModifier: -10,
        maneuversModifier: 10,
        name: SizeName_1.SizeName.colossal,
        occupiedSpaceInMeters: 9,
    },
};
