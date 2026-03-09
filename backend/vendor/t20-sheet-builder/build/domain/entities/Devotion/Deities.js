"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Deities = void 0;
const GrantedPowerName_1 = require("../Power/GrantedPower/GrantedPowerName");
const Race_1 = require("../Race");
const Role_1 = require("../Role");
const DeityName_1 = require("./DeityName");
class Deities {
    static get(name) {
        return Deities.map[name];
    }
    static getAll() {
        return Object.values(Deities.map);
    }
}
exports.Deities = Deities;
Deities.map = {
    aharadak: {
        grantedPowers: [],
        name: DeityName_1.DeityName.aharadak,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: 'all',
    },
    allihanna: {
        grantedPowers: [],
        name: DeityName_1.DeityName.allihanna,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [Race_1.RaceName.dahllan, Race_1.RaceName.elf],
            roles: [],
        },
    },
    azgher: {
        grantedPowers: [],
        name: DeityName_1.DeityName.azgher,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    kallyadranoch: {
        grantedPowers: [],
        name: DeityName_1.DeityName.kallyadranoch,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    khalmyr: {
        grantedPowers: [],
        name: DeityName_1.DeityName.khalmyr,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    lena: {
        grantedPowers: [],
        name: DeityName_1.DeityName.lena,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    linwuh: {
        grantedPowers: [
            GrantedPowerName_1.GrantedPowerName.emptyMind,
        ],
        name: DeityName_1.DeityName.linwuh,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [Race_1.RaceName.dwarf],
            roles: [Role_1.RoleName.warrior],
        },
    },
    marah: {
        grantedPowers: [],
        name: DeityName_1.DeityName.marah,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    megalokk: {
        grantedPowers: [],
        name: DeityName_1.DeityName.megalokk,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    nimb: {
        grantedPowers: [],
        name: DeityName_1.DeityName.nimb,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    sszzzaas: {
        grantedPowers: [],
        name: DeityName_1.DeityName.sszzzaas,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    tannatoh: {
        grantedPowers: [
            GrantedPowerName_1.GrantedPowerName.analyticMind,
        ],
        name: DeityName_1.DeityName.tannatoh,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    thyatis: {
        grantedPowers: [],
        name: DeityName_1.DeityName.thyatis,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    tenebra: {
        grantedPowers: [],
        name: DeityName_1.DeityName.tenebra,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: {
            races: [],
            roles: [],
        },
    },
    thwor: {
        grantedPowers: [],
        name: DeityName_1.DeityName.thwor,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: 'all',
    },
    valkaria: {
        grantedPowers: [],
        name: DeityName_1.DeityName.valkaria,
        beliefsAndGoals: '',
        favoriteWeapon: '',
        sacredSymbol: '',
        allowedToDevote: 'all',
    },
};
