"use client";

import { motion, AnimatePresence, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface MotionWrapperProps extends HTMLMotionProps<"div"> {
    children: ReactNode;
    animation?: "fadeIn" | "scaleIn" | "slideInLeft" | "slideInRight" | "stagger";
    delay?: number;
    className?: string;
}

const variants = {
    fadeIn: {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 },
    },
    scaleIn: {
        hidden: { opacity: 0, scale: 0.9 },
        visible: {
            opacity: 1,
            scale: 1,
            transition: { type: "spring", stiffness: 300, damping: 20 }
        },
    },
    slideInLeft: {
        hidden: { opacity: 0, x: -50 },
        visible: { opacity: 1, x: 0 },
    },
    slideInRight: {
        hidden: { opacity: 0, x: 50 },
        visible: { opacity: 1, x: 0 },
    },
    stagger: {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1
            }
        }
    }
};

export function MotionWrapper({
    children,
    animation = "fadeIn",
    delay = 0,
    className,
    ...props
}: MotionWrapperProps) {
    return (
        <motion.div
            initial="hidden"
            animate="visible"
            exit="hidden"
            variants={variants[animation]}
            transition={{ duration: 0.4, delay }}
            className={cn(className)}
            {...props}
        >
            {children}
        </motion.div>
    );
}

export const MotionItem = motion.div;
