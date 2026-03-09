import { type ArmorName } from './ArmorName';
export declare class Armors {
    static map: {
        chainMail: import("./HeavyArmor").HeavyArmorStatic;
        fullPlate: import("./HeavyArmor").HeavyArmorStatic;
        leatherArmor: import("./LightArmor").LightArmorStatic;
        studdedLeather: import("./LightArmor").LightArmorStatic;
    };
    static get(name: ArmorName): import("./HeavyArmor").HeavyArmorStatic | import("./LightArmor").LightArmorStatic;
    static getAll(): (import("./HeavyArmor").HeavyArmorStatic | import("./LightArmor").LightArmorStatic)[];
}
