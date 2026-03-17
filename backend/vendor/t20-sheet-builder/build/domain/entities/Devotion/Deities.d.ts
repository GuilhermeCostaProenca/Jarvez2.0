import { GrantedPowerName } from '../Power/GrantedPower/GrantedPowerName';
import { RaceName } from '../Race';
import { RoleName } from '../Role';
import { DeityName } from './DeityName';
export type Deity = {
    name: DeityName;
    grantedPowers: GrantedPowerName[];
    beliefsAndGoals: string;
    sacredSymbol: string;
    favoriteWeapon: string;
    allowedToDevote: {
        races: RaceName[];
        roles: RoleName[];
    } | 'all';
};
export declare class Deities {
    static map: Record<DeityName, Deity>;
    static get(name: DeityName): Deity;
    static getAll(): Deity[];
}
