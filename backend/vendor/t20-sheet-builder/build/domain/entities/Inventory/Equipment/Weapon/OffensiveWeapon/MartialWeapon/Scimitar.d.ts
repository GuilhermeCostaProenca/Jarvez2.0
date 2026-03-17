import { Critical } from '../../../../../Attack/Critical';
import { DiceRoll } from '../../../../../Dice/DiceRoll';
import { MartialWeapon } from './MartialWeapon';
import { type MartialWeaponName } from './MartialWeaponName';
export declare class Scimitar extends MartialWeapon {
    static damage: DiceRoll;
    static critical: Critical;
    static equipmentName: MartialWeaponName;
    static purposes: never[];
    static price: number;
    damage: DiceRoll;
    critical: Critical;
    name: MartialWeaponName;
    purposes: never[];
    price: number;
}
