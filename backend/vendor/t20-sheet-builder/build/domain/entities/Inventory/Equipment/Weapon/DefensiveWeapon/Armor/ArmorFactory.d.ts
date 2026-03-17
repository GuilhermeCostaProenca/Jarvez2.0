import { type ArmorName } from './ArmorName';
export declare class ArmorFactory {
    static make(name: ArmorName): import("./HeavyArmor").HeavyArmor | import("./LightArmor").LightArmor;
}
